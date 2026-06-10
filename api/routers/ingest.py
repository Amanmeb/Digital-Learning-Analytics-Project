# Main xAPI ingestion endpoint
# Receives xAPI statements from school sync agents
# Validates, deduplicates, stores in raw schema, forwards to LRS

import os
import uuid
import httpx
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy import text

from api.database import get_db
from api.errors import api_error
from api.fingerprint import calculate_fingerprint
from api.logger import logger, log_to_db
from api.dbt_trigger import trigger_dbt_if_ready

router = APIRouter(tags=["Ingest"])

API_KEY = os.environ.get("API_SECRET_KEY", "")
LRS_ENDPOINT = os.environ.get("LRS_ENDPOINT", "http://localhost:8080/xapi/statements")
LRS_KEY = os.environ.get("LRS_KEY", "")
LRS_SECRET = os.environ.get("LRS_SECRET", "")
SYNC_BATCH_SIZE = int(os.environ.get("SYNC_BATCH_SIZE", "500"))

CAMARA_CONTEXT_EXT = "https://camara.org/xapi/context"
REQUIRED_CAMARA_FIELDS = [
    "school_id", "device_id", "platform_id", "is_offline", "server_id"
]


def validate_api_key(x_api_key=Header(None)):
    # Validates the API key from request header
    if not x_api_key or x_api_key != API_KEY:
        api_error("E001", status_code=401)


def validate_statement(statement):
    # Validates a single xAPI statement structure
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

    context = statement.get("context", {})
    extensions = context.get("extensions", {})
    camara_ext = extensions.get(CAMARA_CONTEXT_EXT, {})
    for field in REQUIRED_CAMARA_FIELDS:
        if field not in camara_ext:
            errors.append("Missing Camara context field: " + field)

    return errors


@router.post("/ingest")
async def ingest_statements(request: Request, db=Depends(get_db)):
    # Receives a batch of xAPI statements from a school sync agent
    # Validates, deduplicates, stores, and forwards to LRS
    request_id = getattr(request.state, "request_id", "unknown")

    # Validate API key
    api_key = request.headers.get("X-API-Key", "")
    if not api_key or api_key != API_KEY:
        api_error("E001", status_code=401)

    # Parse request body
    try:
        body = await request.json()
    except Exception:
        api_error("E004", "Request body is not valid JSON")

    # Handle single statement or batch
    if isinstance(body, dict):
        statements = [body]
    elif isinstance(body, list):
        statements = body
    else:
        api_error("E004", "Expected JSON object or array")

    # Check batch size
    if len(statements) > SYNC_BATCH_SIZE:
        api_error("E011", "Maximum batch size is " + str(SYNC_BATCH_SIZE))

    # Get server and school from first statement
    server_id = "unknown"
    school_id = "unknown"
    if statements:
        context = statements[0].get("context", {})
        extensions = context.get("extensions", {})
        camara_ext = extensions.get(CAMARA_CONTEXT_EXT, {})
        server_id = camara_ext.get("server_id", "unknown")
        school_id = camara_ext.get("school_id", "unknown")

    received = len(statements)
    inserted = 0
    duplicate = 0
    rejected = 0
    lrs_statements = []

    now = datetime.now(timezone.utc)

    for statement in statements:
        # Validate statement
        errors = validate_statement(statement)
        if errors:
            rejected += 1
            logger.warning("Statement rejected: " + str(errors))
            continue

        # Calculate fingerprint for deduplication
        fingerprint = calculate_fingerprint(statement)
        if not fingerprint:
            rejected += 1
            continue

        # Check for duplicate
        existing = db.execute(
            text("SELECT 1 FROM raw.xapi_statements WHERE event_fingerprint = :fp"),
            {"fp": fingerprint}
        ).fetchone()

        if existing:
            duplicate += 1
            continue

        # Insert into raw schema
        statement_id = statement.get("id", str(uuid.uuid4()))
        try:
            db.execute(
                text("""
                    INSERT INTO raw.xapi_statements
                        (statement_id, server_id, school_id, actor, verb,
                         object, result, context, timestamp, event_fingerprint)
                    VALUES
                        (:statement_id, :server_id, :school_id, :actor, :verb,
                         :object, :result, :context, :timestamp, :event_fingerprint)
                """),
                {
                    "statement_id":      statement_id,
                    "server_id":         server_id,
                    "school_id":         school_id,
                    "actor":             json.dumps(statement.get("actor", {})),
                    "verb":              json.dumps(statement.get("verb", {})),
                    "object":            json.dumps(statement.get("object", {})),
                    "result":            json.dumps(statement.get("result")) if statement.get("result") else None,
                    "context":           json.dumps(statement.get("context")) if statement.get("context") else None,
                    "timestamp":         statement.get("timestamp"),
                    "event_fingerprint": fingerprint,
                }
            )
            db.commit()
            inserted += 1
            lrs_statements.append(statement)
        except Exception as e:
            db.rollback()
            rejected += 1
            logger.error("Insert failed: " + str(e))

    # Forward valid statements to LRS
    lrs_ok = False
    if lrs_statements and LRS_KEY and LRS_SECRET:
        try:
            import base64
            credentials = base64.b64encode(
                (LRS_KEY + ":" + LRS_SECRET).encode()
            ).decode()
            async with httpx.AsyncClient(timeout=30) as client:
                lrs_response = await client.post(
                    LRS_ENDPOINT,
                    json=lrs_statements if len(lrs_statements) > 1 else lrs_statements[0],
                    headers={
                        "Authorization":             "Basic " + credentials,
                        "Content-Type":              "application/json",
                        "X-Experience-API-Version":  "1.0.3",
                    }
                )
            lrs_ok = lrs_response.status_code in (200, 204)
        except Exception as e:
            logger.warning("LRS forward failed: " + str(e))

    # Write sync log entry
    sync_id = "SYNC-" + str(uuid.uuid4())
    try:
        db.execute(
            text("""
                INSERT INTO ops.sync_log
                    (sync_id, server_id, school_id, request_id,
                     statements_received, statements_inserted,
                     statements_rejected, statements_duplicate,
                     import_source, status)
                VALUES
                    (:sync_id, :server_id, :school_id, :request_id,
                     :received, :inserted, :rejected, :duplicate,
                     :source, :status)
            """),
            {
                "sync_id":    sync_id,
                "server_id":  server_id,
                "school_id":  school_id,
                "request_id": request_id,
                "received":   received,
                "inserted":   inserted,
                "rejected":   rejected,
                "duplicate":  duplicate,
                "source":     "sync_agent",
                "status":     "ok" if rejected == 0 else "partial",
            }
        )
        db.commit()
    except Exception as e:
        logger.warning("Sync log write failed: " + str(e))

    log_to_db(
        db, "INFO", "ingest",
        "Batch processed",
        school_id=school_id,
        request_id=request_id,
        details="received=" + str(received) + " inserted=" + str(inserted) +
                " duplicate=" + str(duplicate) + " rejected=" + str(rejected),
    )

    # Trigger dbt run if statements were inserted
    if inserted > 0:
        trigger_dbt_if_ready()

    return {
        "request_id":            request_id,
        "statements_received":   received,
        "statements_inserted":   inserted,
        "statements_duplicate":  duplicate,
        "statements_rejected":   rejected,
        "lrs_forwarded":         lrs_ok,
    }
