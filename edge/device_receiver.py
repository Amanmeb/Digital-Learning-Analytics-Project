# CDLAID Device Receiver
# Lightweight FastAPI app running on school server port 8000
# Accepts xAPI events from student devices on the hotspot
# Runs same SHA-256 fingerprint deduplication as central API
# Stores valid events in school SQLite queue
# Triggers school dbt run after successful insert with 5-minute cooldown

import hashlib
import json
import logging
import os
import subprocess
import threading
import time
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from edge.queue_manager import create_tables, insert_event, get_queue_depth

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

SCHOOL_ID        = os.environ.get("SCHOOL_ID", "ET-AA-001")
SERVER_ID        = os.environ.get("SERVER_ID", "SRV-ET-AA-001-001")
SCHOOL_API_KEY   = os.environ.get("SCHOOL_API_KEY", "")
DBT_PROJECT_DIR  = os.environ.get("DBT_PROJECT_DIR", "/opt/cdlaid/cdlaid_dbt")
DBT_PROFILES_DIR = os.environ.get("DBT_PROFILES_DIR", "/opt/cdlaid/cdlaid_dbt")
DBT_COOLDOWN_SECONDS = 300

CAMARA_CONTEXT_EXT = "https://camara.org/xapi/context"

REQUIRED_CAMARA_FIELDS = [
    "school_id",
    "device_id",
    "platform_id",
    "is_offline",
    "server_id",
    "tracking_depth",
]

# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] device_receiver: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("device_receiver")

# ------------------------------------------------------------
# dbt trigger with 5-minute cooldown
# Same pattern as api/dbt_trigger.py
# ------------------------------------------------------------

_last_dbt_run    = 0
_dbt_lock        = threading.Lock()
_dbt_scheduled   = False


def _run_dbt():
    # Runs school dbt in a subprocess and logs result
    global _last_dbt_run, _dbt_scheduled
    try:
        logger.info("dbt trigger: starting school run")
        start = time.time()
        result = subprocess.run(
            [
                "dbt", "run",
                "--project-dir", DBT_PROJECT_DIR,
                "--profiles-dir", DBT_PROFILES_DIR,
                "--profile", "cdlaid_dbt",
                "--target", "school",
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
        duration = round(time.time() - start, 1)
        if result.returncode == 0:
            logger.info(
                "dbt trigger: completed successfully in " + str(duration) + "s"
            )
        else:
            logger.error(
                "dbt trigger: failed after " + str(duration) + "s -- " +
                result.stderr[-500:]
            )
    except subprocess.TimeoutExpired:
        logger.error("dbt trigger: timed out after 600 seconds")
    except Exception as e:
        logger.error("dbt trigger: error -- " + str(e))
    finally:
        _last_dbt_run  = time.time()
        _dbt_scheduled = False


def trigger_dbt_if_ready():
    # Triggers school dbt run if cooldown has passed
    global _last_dbt_run, _dbt_scheduled
    now = time.time()
    with _dbt_lock:
        if _dbt_scheduled:
            return
        time_since_last = now - _last_dbt_run
        if time_since_last >= DBT_COOLDOWN_SECONDS:
            _dbt_scheduled = True
            thread = threading.Thread(target=_run_dbt, daemon=True)
            thread.start()
            logger.info("dbt trigger: queued immediately")
        else:
            wait_seconds = DBT_COOLDOWN_SECONDS - time_since_last
            _dbt_scheduled = True
            def delayed_run():
                time.sleep(wait_seconds)
                _run_dbt()
            thread = threading.Thread(target=delayed_run, daemon=True)
            thread.start()
            logger.info(
                "dbt trigger: scheduled in " + str(round(wait_seconds)) + "s"
            )


# ------------------------------------------------------------
# Fingerprint calculation
# Same formula as central API and device agent
# ------------------------------------------------------------

def calculate_fingerprint(statement):
    # SHA-256 of student_id|event_type|content_id|timestamp|school_id
    try:
        camara_ext = (
            statement
            .get("context", {})
            .get("extensions", {})
            .get(CAMARA_CONTEXT_EXT, {})
        )
        student_id = statement.get("actor", {}).get("account", {}).get("name", "")
        event_type = statement.get("verb", {}).get("id", "")
        content_id = statement.get("object", {}).get("id", "")
        timestamp  = statement.get("timestamp", "")
        school_id  = camara_ext.get("school_id", "")

        raw = (
            student_id + "|" +
            event_type + "|" +
            content_id + "|" +
            timestamp  + "|" +
            school_id
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
    except Exception:
        return ""


# ------------------------------------------------------------
# Statement validation
# ------------------------------------------------------------

def validate_statement(statement):
    # Returns list of errors -- empty list means valid
    errors = []

    if "actor" not in statement:
        errors.append("Missing actor")
    else:
        actor = statement["actor"]
        if "account" not in actor and "mbox" not in actor:
            errors.append("Actor missing account or mbox")

    if "verb" not in statement or "id" not in statement.get("verb", {}):
        errors.append("Missing verb id")

    if "object" not in statement or "id" not in statement.get("object", {}):
        errors.append("Missing object id")

    if "timestamp" not in statement:
        errors.append("Missing timestamp")

    context    = statement.get("context", {})
    extensions = context.get("extensions", {})
    camara_ext = extensions.get(CAMARA_CONTEXT_EXT, {})
    for field in REQUIRED_CAMARA_FIELDS:
        if field not in camara_ext:
            errors.append("Missing Camara context field: " + field)

    return errors


# ------------------------------------------------------------
# FastAPI app
# ------------------------------------------------------------

app = FastAPI(
    title="CDLAID Device Receiver",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    # Creates SQLite queue tables on startup
    create_tables()
    logger.info("Device receiver starting")
    logger.info("School ID: " + SCHOOL_ID)
    logger.info("Server ID: " + SERVER_ID)
    logger.info("Queue ready")


@app.get("/api/v1/ping")
def ping():
    # Health check endpoint
    # Device agent uses this to detect school server reachability
    return {
        "status":     "ok",
        "school_id":  SCHOOL_ID,
        "server_id":  SERVER_ID,
        "queue_depth": get_queue_depth(),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/v1/device/ingest")
async def device_ingest(request: Request):
    # Receives xAPI statements from student devices
    # Validates, deduplicates, stores in school SQLite queue
    # Triggers school dbt run after successful insert

    # Validate API key
    api_key = request.headers.get("X-API-Key", "")
    if SCHOOL_API_KEY and api_key != SCHOOL_API_KEY:
        return {"error": "Invalid API key"}

    # Parse request body
    try:
        body = await request.json()
    except Exception:
        return {"error": "Request body is not valid JSON"}

    # Handle single statement or batch
    if isinstance(body, dict):
        statements = [body]
    elif isinstance(body, list):
        statements = body
    else:
        return {"error": "Expected JSON object or array"}

    received  = len(statements)
    inserted  = 0
    duplicate = 0
    rejected  = 0

    for statement in statements:
        # Validate statement
        errors = validate_statement(statement)
        if errors:
            rejected += 1
            logger.warning("Statement rejected: " + str(errors))
            continue

        # Calculate fingerprint
        fingerprint = calculate_fingerprint(statement)
        if not fingerprint:
            rejected += 1
            logger.warning("Fingerprint calculation failed -- statement rejected")
            continue

        # Insert into school SQLite queue
        # insert_event returns False if fingerprint already exists
        was_inserted = insert_event(fingerprint, statement)
        if was_inserted:
            inserted += 1
        else:
            duplicate += 1

    logger.info(
        "Device ingest: received=" + str(received) +
        " inserted=" + str(inserted) +
        " duplicate=" + str(duplicate) +
        " rejected=" + str(rejected)
    )

    # Trigger school dbt run if statements were inserted
    if inserted > 0:
        trigger_dbt_if_ready()

    return {
        "statements_received":  received,
        "statements_inserted":  inserted,
        "statements_duplicate": duplicate,
        "statements_rejected":  rejected,
        "school_id":            SCHOOL_ID,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)