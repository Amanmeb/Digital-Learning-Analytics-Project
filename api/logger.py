# Structured logging for the CDLAID ingestion API
# Writes to both console and ops.system_log table in PostgreSQL
# Used by all routers and middleware

import logging
import os
from datetime import datetime, timezone
from sqlalchemy import text

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("cdlaid")


def log_to_db(
    db,
    level,
    component,
    event,
    school_id=None,
    request_id=None,
    details=None,
    duration_ms=None,
):
    # Writes a log entry to ops.system_log table
    # Fails silently so logging never breaks the main request
    try:
        now = datetime.now(timezone.utc)
        db.execute(
            text("""
                INSERT INTO ops.system_log
                    (log_time, log_level, component, school_id, event,
                     duration_ms, request_id, details)
                VALUES
                    (:log_time, :log_level, :component, :school_id, :event,
                     :duration_ms, :request_id, :details)
            """),
            {
                "log_time":    now,
                "log_level":   level,
                "component":   component,
                "school_id":   school_id,
                "event":       event,
                "duration_ms": duration_ms,
                "request_id":  request_id,
                "details":     details,
            }
        )
        db.commit()
    except Exception as e:
        logger.warning("Failed to write to system_log: " + str(e))


def log_to_audit(
    db,
    user_name,
    action,
    role_name=None,
    school_id=None,
    table_name=None,
    record_count=None,
    request_id=None,
    details=None,
):
    # Writes an audit entry to ops.audit_log table
    # Used for all sensitive actions like school registration and imports
    try:
        now = datetime.now(timezone.utc)
        db.execute(
            text("""
                INSERT INTO ops.audit_log
                    (event_time, user_name, role_name, school_id, action,
                     table_name, record_count, request_id, details)
                VALUES
                    (:event_time, :user_name, :role_name, :school_id, :action,
                     :table_name, :record_count, :request_id, :details)
            """),
            {
                "event_time":   now,
                "user_name":    user_name,
                "role_name":    role_name,
                "school_id":    school_id,
                "action":       action,
                "table_name":   table_name,
                "record_count": record_count,
                "request_id":   request_id,
                "details":      details,
            }
        )
        db.commit()
    except Exception as e:
        logger.warning("Failed to write to audit_log: " + str(e))