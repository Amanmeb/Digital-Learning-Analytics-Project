# CDLAID Device Agent
# Lightweight background service for student devices
# Stores xAPI events locally and uploads to school server when hotspot detected
# Runs as Windows Service or Linux systemd service
# No internet required -- works fully offline
# Uploads to http://10.42.0.1:8000/api/v1/device/ingest when hotspot detected

import hashlib
import json
import logging
import os
import platform
import socket
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# ------------------------------------------------------------
# Configuration from environment variables
# Set by install_device.bat or install_device.sh at install time
# ------------------------------------------------------------

SCHOOL_ID       = os.environ.get("SCHOOL_ID", "ET-AA-001")
SERVER_ID       = os.environ.get("SERVER_ID", "SRV-ET-AA-001-001")
DEVICE_ID       = os.environ.get("DEVICE_ID", "DEV-ET-AA-001-000001")
SCHOOL_API_KEY  = os.environ.get("SCHOOL_API_KEY", "")
RECEIVER_URL    = os.environ.get(
    "RECEIVER_URL",
    "http://10.42.0.1:8000/api/v1/device/ingest",
)
HOTSPOT_IP      = os.environ.get("HOTSPOT_IP", "10.42.0.1")
SYNC_INTERVAL   = int(os.environ.get("SYNC_INTERVAL_SECONDS", "60"))
BATCH_SIZE      = int(os.environ.get("SYNC_BATCH_SIZE", "200"))

MAX_RETRY_ATTEMPTS  = 5
RETRY_BACKOFF_BASE  = 2

# ------------------------------------------------------------
# SQLite queue path -- platform specific
# ------------------------------------------------------------

def get_queue_path():
    # Returns platform-specific path for the local SQLite queue
    # Windows: C:\cdlaid\device_queue.db
    # Linux:   /opt/cdlaid/device_queue.db
    if platform.system() == "Windows":
        return Path("C:\\cdlaid\\device_queue.db")
    return Path("/opt/cdlaid/device_queue.db")


QUEUE_DB_PATH = Path(os.environ.get("DEVICE_QUEUE_PATH", str(get_queue_path())))

# ------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] device_agent: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("device_agent")

# ------------------------------------------------------------
# SQLite queue management
# Self-contained -- does not import from edge/queue_manager.py
# ------------------------------------------------------------

def get_connection():
    # Creates parent directory if it does not exist
    QUEUE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(QUEUE_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    # Creates local queue tables if they do not exist
    # Safe to call multiple times
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fingerprint TEXT UNIQUE NOT NULL,
            statement   TEXT NOT NULL,
            synced      INTEGER DEFAULT 0,
            created_at  TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sync_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_started_at TEXT NOT NULL,
            sync_ended_at   TEXT,
            records_sent    INTEGER DEFAULT 0,
            records_ok      INTEGER DEFAULT 0,
            records_failed  INTEGER DEFAULT 0,
            status          TEXT DEFAULT 'pending',
            error_message   TEXT
        );
    """)
    conn.commit()
    conn.close()


def calculate_fingerprint(statement):
    # Calculates SHA-256 fingerprint matching the central formula
    # Formula: SHA-256 of student_id|event_type|content_id|timestamp|school_id
    try:
        camara_ext = (
            statement
            .get("context", {})
            .get("extensions", {})
            .get("https://camara.org/xapi/context", {})
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


def insert_event(statement):
    # Inserts a new xAPI event into the local queue
    # Returns True if inserted, False if duplicate fingerprint
    fingerprint = calculate_fingerprint(statement)
    if not fingerprint:
        logger.warning("Could not calculate fingerprint -- event skipped")
        return False

    conn = get_connection()
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT OR IGNORE INTO events "
            "(fingerprint, statement, created_at) VALUES (?, ?, ?)",
            (fingerprint, json.dumps(statement), now)
        )
        conn.commit()
        inserted = conn.total_changes > 0
        if inserted:
            logger.info("Event queued: " + fingerprint[:16] + "...")
        else:
            logger.info("Duplicate event skipped: " + fingerprint[:16] + "...")
        return inserted
    finally:
        conn.close()


def read_batch():
    # Returns a batch of unsynced events up to BATCH_SIZE
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, fingerprint, statement FROM events "
            "WHERE synced = 0 ORDER BY id ASC LIMIT ?",
            (BATCH_SIZE,)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def mark_synced(event_ids):
    # Marks confirmed events as synced
    # Only called after school server confirms receipt
    # Events are never deleted -- only marked synced
    if not event_ids:
        return
    conn = get_connection()
    try:
        placeholders = ",".join("?" * len(event_ids))
        conn.execute(
            "UPDATE events SET synced = 1 WHERE id IN (" + placeholders + ")",
            event_ids
        )
        conn.commit()
    finally:
        conn.close()


def get_queue_depth():
    # Returns count of unsynced events
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) as count FROM events WHERE synced = 0"
        ).fetchone()
        return row["count"] if row else 0
    finally:
        conn.close()


def log_sync(records_sent, records_ok, records_failed, status, error_message=None):
    # Records a sync attempt in the local sync log
    conn = get_connection()
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO sync_log "
            "(sync_started_at, sync_ended_at, records_sent, records_ok, "
            "records_failed, status, error_message) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (now, now, records_sent, records_ok, records_failed, status, error_message)
        )
        conn.commit()
    finally:
        conn.close()


# ------------------------------------------------------------
# Network detection
# ------------------------------------------------------------

def is_hotspot_reachable():
    # Checks if school hotspot is reachable by connecting to port 8000
    # Uses a short timeout so the check is fast
    try:
        sock = socket.create_connection((HOTSPOT_IP, 8000), timeout=3)
        sock.close()
        return True
    except (socket.timeout, socket.error, OSError):
        return False


# ------------------------------------------------------------
# Upload
# ------------------------------------------------------------

def upload_batch(batch):
    # Uploads a batch of statements to the school device receiver
    # Returns (success, inserted_count, error_message)
    if not batch:
        return True, 0, None

    statements = [json.loads(event["statement"]) for event in batch]

    headers = {
        "X-API-Key":    SCHOOL_API_KEY,
        "X-School-ID":  SCHOOL_ID,
        "X-Device-ID":  DEVICE_ID,
        "Content-Type": "application/json",
    }

    for attempt in range(MAX_RETRY_ATTEMPTS):
        try:
            response = requests.post(
                RECEIVER_URL,
                json=statements,
                headers=headers,
                timeout=30,
            )
            if response.status_code == 200:
                result = response.json()
                inserted = result.get("statements_inserted", 0)
                logger.info(
                    "Upload successful: " + str(inserted) +
                    " inserted of " + str(len(batch)) + " sent"
                )
                return True, inserted, None
            else:
                error = "HTTP " + str(response.status_code)
                logger.warning(
                    "Upload failed: " + error +
                    " attempt " + str(attempt + 1)
                )
        except requests.exceptions.ConnectionError:
            logger.warning(
                "Connection lost during upload -- attempt " + str(attempt + 1)
            )
        except requests.exceptions.Timeout:
            logger.warning(
                "Upload timed out -- attempt " + str(attempt + 1)
            )
        except Exception as e:
            logger.warning(
                "Upload error: " + str(e) +
                " attempt " + str(attempt + 1)
            )

        # Exponential backoff between retries
        wait = RETRY_BACKOFF_BASE ** attempt
        logger.info("Retrying in " + str(wait) + " seconds")
        time.sleep(wait)

    return False, 0, "Max retry attempts reached"


# ------------------------------------------------------------
# Sync cycle
# ------------------------------------------------------------

def sync_once():
    # Performs a single sync cycle
    # Reads batch from local queue and uploads to school server
    depth = get_queue_depth()
    if depth == 0:
        logger.info("Queue is empty -- nothing to sync")
        return

    logger.info("Queue depth: " + str(depth) + " -- starting upload")

    batch = read_batch()
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
        logger.info(
            "Sync complete: " + str(len(batch)) + " sent, " +
            str(inserted) + " confirmed"
        )
    else:
        log_sync(
            records_sent=len(batch),
            records_ok=0,
            records_failed=len(batch),
            status="failed",
            error_message=error,
        )
        logger.warning("Sync failed: " + str(error))


# ------------------------------------------------------------
# Main loop
# ------------------------------------------------------------

def run():
    # Main agent loop
    # Checks hotspot reachability every SYNC_INTERVAL seconds
    # Syncs when hotspot is detected
    logger.info("CDLAID Device Agent starting")
    logger.info("Device ID:  " + DEVICE_ID)
    logger.info("School ID:  " + SCHOOL_ID)
    logger.info("Hotspot IP: " + HOTSPOT_IP)
    logger.info("Queue path: " + str(QUEUE_DB_PATH))
    logger.info("Receiver:   " + RECEIVER_URL)

    create_tables()

    while True:
        if is_hotspot_reachable():
            logger.info("Hotspot reachable -- syncing")
            sync_once()
        else:
            logger.info("Hotspot not reachable -- working offline")

        logger.info("Next check in " + str(SYNC_INTERVAL) + " seconds")
        time.sleep(SYNC_INTERVAL)


if __name__ == "__main__":
    run()