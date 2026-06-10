# Sync agent for school servers
# Reads from SQLite queue and uploads to central FastAPI
# Runs as a systemd service on Linux school servers
# Also works on Windows and Mac for development
#
# Backlog alerts:
#   BACKLOG_ALERT_LOW  = 3 days  (warning)
#   BACKLOG_ALERT_MID  = 7 days  (medium alert)
#   BACKLOG_ALERT_HIGH = 15 days (critical alert)

import json
import logging
import os
import time
import gzip
import requests
from datetime import datetime, timezone, timedelta

from edge.queue_manager import (
    create_tables,
    read_batch,
    mark_synced,
    quarantine_event,
    get_queue_depth,
    get_last_sync,
    log_sync,
    register_device,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] sync_agent: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sync_agent")

CENTRAL_API_URL  = os.environ.get("CENTRAL_API_URL", "http://localhost:8000")
API_KEY          = os.environ.get("API_SECRET_KEY", "")
SCHOOL_ID        = os.environ.get("SCHOOL_ID", "ET-AA-001")
SERVER_ID        = os.environ.get("SERVER_ID", "SRV-ET-AA-001-001")
DEVICE_ID        = os.environ.get("DEVICE_ID", "DEV-ET-AA-001-000001")
SYNC_BATCH_SIZE  = int(os.environ.get("SYNC_BATCH_SIZE", "500"))
SYNC_INTERVAL    = int(os.environ.get("SYNC_INTERVAL_SECONDS", "300"))

BACKLOG_ALERT_LOW  = int(os.environ.get("BACKLOG_ALERT_LOW", "3"))
BACKLOG_ALERT_MID  = int(os.environ.get("BACKLOG_ALERT_MID", "7"))
BACKLOG_ALERT_HIGH = int(os.environ.get("BACKLOG_ALERT_HIGH", "15"))

MAX_RETRY_ATTEMPTS = 5
RETRY_BACKOFF_BASE = 2


def check_connectivity():
    # Returns True if central server is reachable
    try:
        response = requests.get(
            CENTRAL_API_URL + "/api/v1/ping",
            timeout=10,
        )
        return response.status_code == 200
    except Exception:
        return False


def check_backlog_alert():
    # Checks how many days since last successful sync
    # Returns alert level: none, low, medium, high
    last_sync = get_last_sync()
    if not last_sync:
        return "none"

    last_sync_time = datetime.fromisoformat(last_sync["sync_ended_at"])
    if last_sync_time.tzinfo is None:
        last_sync_time = last_sync_time.replace(tzinfo=timezone.utc)

    days_since_sync = (datetime.now(timezone.utc) - last_sync_time).days

    if days_since_sync >= BACKLOG_ALERT_HIGH:
        return "high"
    elif days_since_sync >= BACKLOG_ALERT_MID:
        return "medium"
    elif days_since_sync >= BACKLOG_ALERT_LOW:
        return "low"
    return "none"


def upload_batch(batch):
    # Uploads a batch of statements to the central API
    # Returns (success, inserted_count, error_message)
    if not batch:
        return True, 0, None

    statements = [json.loads(event["statement"]) for event in batch]

    headers = {
        "X-API-Key":    API_KEY,
        "Content-Type": "application/json",
        "X-School-ID":  SCHOOL_ID,
    }

    for attempt in range(MAX_RETRY_ATTEMPTS):
        try:
            response = requests.post(
                CENTRAL_API_URL + "/api/v1/ingest",
                json=statements,
                headers=headers,
                timeout=60,
            )
            if response.status_code == 200:
                result = response.json()
                return True, result.get("statements_inserted", 0), None
            else:
                error = "HTTP " + str(response.status_code)
                logger.warning("Upload failed: " + error + " attempt " + str(attempt + 1))
        except Exception as e:
            logger.warning("Upload error: " + str(e) + " attempt " + str(attempt + 1))

        # Exponential backoff
        wait = RETRY_BACKOFF_BASE ** attempt
        logger.info("Retrying in " + str(wait) + " seconds")
        time.sleep(wait)

    return False, 0, "Max retry attempts reached"


def sync_once():
    # Performs a single sync cycle
    # Reads batch, uploads, marks synced
    queue_depth = get_queue_depth()
    if queue_depth == 0:
        logger.info("Queue is empty -- nothing to sync")
        return

    logger.info("Queue depth: " + str(queue_depth) + " -- starting sync")

    batch = read_batch(SYNC_BATCH_SIZE)
    if not batch:
        return

    success, inserted, error = upload_batch(batch)

    if success:
        event_ids = [event["id"] for event in batch]
        mark_synced(event_ids)
        log_sync(
            records_sent=len(batch),
            records_ok=inserted,
            records_failed=len(batch) - inserted,
            status="ok",
        )
        logger.info("Sync complete: " + str(inserted) + " inserted")
    else:
        log_sync(
            records_sent=len(batch),
            records_ok=0,
            records_failed=len(batch),
            status="failed",
            error_message=error,
        )
        logger.error("Sync failed: " + str(error))

    alert = check_backlog_alert()
    if alert != "none":
        logger.warning("Backlog alert level: " + alert)


def run():
    # Main sync loop -- runs continuously
    # Checks connectivity before each sync attempt
    logger.info("Sync agent starting")
    logger.info("School ID: " + SCHOOL_ID)
    logger.info("Server ID: " + SERVER_ID)
    logger.info("Central API: " + CENTRAL_API_URL)

    create_tables()
    register_device(DEVICE_ID, SCHOOL_ID, SERVER_ID)

    while True:
        if check_connectivity():
            logger.info("Central server reachable -- syncing")
            sync_once()
        else:
            logger.info("Central server not reachable -- working offline")

        logger.info("Next sync in " + str(SYNC_INTERVAL) + " seconds")
        time.sleep(SYNC_INTERVAL)


if __name__ == "__main__":
    run()
