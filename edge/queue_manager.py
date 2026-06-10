# SQLite queue manager for school servers
# Handles all local event storage before sync to central server
# Works fully offline -- no internet required
# Tables: events, quarantine, sync_log, device_registry

import json
import sqlite3
import os
from datetime import datetime, timezone
from pathlib import Path

QUEUE_DB_PATH = Path(os.environ.get("QUEUE_DB_PATH", "edge/queue.db"))


def get_connection():
    # Creates parent directory if it does not exist
    # Works on Windows, Linux, and Mac
    QUEUE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(QUEUE_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    # Creates all required tables if they do not exist
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

        CREATE TABLE IF NOT EXISTS quarantine (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            statement  TEXT NOT NULL,
            errors     TEXT NOT NULL,
            created_at TEXT NOT NULL
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

        CREATE TABLE IF NOT EXISTS device_registry (
            device_id       TEXT PRIMARY KEY,
            school_id       TEXT NOT NULL,
            server_id       TEXT NOT NULL,
            registered_at   TEXT NOT NULL,
            last_seen_at    TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def insert_event(fingerprint, statement):
    # Inserts a new event into the queue
    # Returns True if inserted, False if duplicate
    conn = get_connection()
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT OR IGNORE INTO events (fingerprint, statement, created_at) "
            "VALUES (?, ?, ?)",
            (fingerprint, json.dumps(statement), now)
        )
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def read_batch(batch_size=500):
    # Returns a batch of unsynced events
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, fingerprint, statement FROM events "
            "WHERE synced = 0 ORDER BY id ASC LIMIT ?",
            (batch_size,)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def mark_synced(event_ids):
    # Marks a list of event IDs as successfully synced
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


def quarantine_event(statement, errors):
    # Moves an invalid event to the quarantine table
    conn = get_connection()
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO quarantine (statement, errors, created_at) VALUES (?, ?, ?)",
            (json.dumps(statement), json.dumps(errors), now)
        )
        conn.commit()
    finally:
        conn.close()


def get_queue_depth():
    # Returns count of unsynced events in the queue
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) as count FROM events WHERE synced = 0"
        ).fetchone()
        return row["count"] if row else 0
    finally:
        conn.close()


def get_last_sync():
    # Returns the most recent sync log entry
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM sync_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None
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


def register_device(device_id, school_id, server_id):
    # Registers or updates a device in the local device registry
    conn = get_connection()
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO device_registry "
            "(device_id, school_id, server_id, registered_at, last_seen_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(device_id) DO UPDATE SET last_seen_at = ?",
            (device_id, school_id, server_id, now, now, now)
        )
        conn.commit()
    finally:
        conn.close()


def get_db_path():
    # Returns the path to the SQLite queue database
    return str(QUEUE_DB_PATH)