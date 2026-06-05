

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from xapi.validator import (
    validate_statement,
    validate_completion_status,
    validate_query_type,
    calculate_fingerprint,
)


# Read all dynamic values from environment variables
# pathlib.Path handles all OS path separators automatically
QUEUE_DB_PATH     = Path(os.environ.get("QUEUE_DB_PATH", "edge/queue.db"))
XAPI_HOMEPAGE_URL = os.environ.get("XAPI_HOMEPAGE_URL", "http://localhost:3000")
XAPI_SERVER_ID    = os.environ.get("XAPI_SERVER_ID", "SRV-ET-AA-001-001")
XAPI_SCHOOL_ID    = os.environ.get("XAPI_SCHOOL_ID", "ET-AA-001")

# xAPI URI constants -- these are international standards and never change
CAMARA_CONTEXT_EXT = "https://camara.org/xapi/context"
CAMARA_VERB_BASE   = "https://camara.org/xapi/verbs"
ADLNET_VERB_BASE   = "http://adlnet.gov/expapi/verbs"
ACTIVITY_BASE      = "https://camara.org/xapi/activities"


def _get_connection():
    # Create parent directory if it does not exist
    # parents=True creates all intermediate directories
    # exist_ok=True does not raise error if directory already exists

    QUEUE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(QUEUE_DB_PATH))

    # Events table -- holds all valid xAPI statements waiting to sync
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            fingerprint TEXT UNIQUE NOT NULL,
            statement   TEXT NOT NULL,
            synced      INTEGER DEFAULT 0,
            created_at  TEXT NOT NULL
        )
    """)

    # Quarantine table -- holds invalid statements with error details
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quarantine (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            statement  TEXT NOT NULL,
            errors     TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    return conn


def _now():
    # Returns current UTC time in ISO 8601 format with Z suffix

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _build_actor(student_id):
    # Builds xAPI actor object using student ID and homepage from environment
    # homePage is dynamic -- set XAPI_HOMEPAGE_URL in .env for each country
    return {
        "objectType": "Agent",
        "account": {
            "name": student_id,
            "homePage": XAPI_HOMEPAGE_URL,
        },
    }


def _build_camara_context(
    school_id,
    device_id,
    platform_id,
    is_offline,
    server_id,
    tracking_depth,
    extra=None,
):
    # Builds Camara custom context extension

    ext = {
        "school_id":      school_id,
        "device_id":      device_id,
        "platform_id":    platform_id,
        "is_offline":     is_offline,
        "server_id":      server_id,
        "tracking_depth": tracking_depth,
    }
    if extra:
        ext.update(extra)
    return {
        "extensions": {
            CAMARA_CONTEXT_EXT: ext,
        }
    }


def _quarantine(statement, errors):
    # Writes invalid statement to quarantine table with error details
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO quarantine (statement, errors, created_at) "
            "VALUES (?, ?, ?)",
            (json.dumps(statement), json.dumps(errors), _now()),
        )
        conn.commit()
    finally:
        conn.close()


def _emit(statement):
    # Central emit function called by all public emit functions
    # Step 1 -- validate full statement structure
    is_valid, errors = validate_statement(statement)
    if not is_valid:
        _quarantine(statement, errors)
        return False

    # Step 2 -- calculate SHA-256 fingerprint for deduplication
    fingerprint = calculate_fingerprint(statement)
    if not fingerprint:
        _quarantine(statement, ["Fingerprint calculation failed"])
        return False

    # Step 3 -- insert into queue
    # INSERT OR IGNORE silently skips if fingerprint already exists
    # This is the first deduplication layer -- FastAPI is the second
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO events "
            "(fingerprint, statement, created_at) VALUES (?, ?, ?)",
            (fingerprint, json.dumps(statement), _now()),
        )
        conn.commit()
    finally:
        conn.close()
    return True


def emit_session_start(
    student_id,
    school_id,
    device_id,
    platform_id,
    server_id,
    is_offline,
    session_id,
    tracking_depth="full",
):
    # Emits a session-started event
    # Called when a student begins a learning session on any platform
    statement = {
        "id":        str(uuid.uuid4()),
        "timestamp": _now(),
        "actor":     _build_actor(student_id),
        "verb": {
            "id":      CAMARA_VERB_BASE + "/session-started",
            "display": {"en-US": "started session"},
        },
        "object": {
            "id":         ACTIVITY_BASE + "/session/" + session_id,
            "objectType": "Activity",
            "definition": {
                "type": ACTIVITY_BASE + "/types/session",
            },
        },
        "context": _build_camara_context(
            school_id, device_id, platform_id,
            is_offline, server_id, tracking_depth,
        ),
    }
    return _emit(statement)


def emit_session_end(
    student_id,
    school_id,
    device_id,
    platform_id,
    server_id,
    is_offline,
    session_id,
    duration_seconds,
    tracking_depth="full",
):
    # Emits a session-ended event

    statement = {
        "id":        str(uuid.uuid4()),
        "timestamp": _now(),
        "actor":     _build_actor(student_id),
        "verb": {
            "id":      CAMARA_VERB_BASE + "/session-ended",
            "display": {"en-US": "ended session"},
        },
        "object": {
            "id":         ACTIVITY_BASE + "/session/" + session_id,
            "objectType": "Activity",
            "definition": {
                "type": ACTIVITY_BASE + "/types/session",
            },
        },
        "result": {
            "duration": "PT" + str(duration_seconds) + "S",
        },
        "context": _build_camara_context(
            school_id, device_id, platform_id,
            is_offline, server_id, tracking_depth,
        ),
    }
    return _emit(statement)


def emit_content_accessed(
    student_id,
    school_id,
    device_id,
    platform_id,
    server_id,
    is_offline,
    content_id,
    content_name,
    tracking_depth="full",
):
    # Emits a content accessed event
    # Called when a student opens any content item on any platform
    # This is the only emit function available for click-only platforms
    statement = {
        "id":        str(uuid.uuid4()),
        "timestamp": _now(),
        "actor":     _build_actor(student_id),
        "verb": {
            "id":      ADLNET_VERB_BASE + "/experienced",
            "display": {"en-US": "accessed"},
        },
        "object": {
            "id":         content_id,
            "objectType": "Activity",
            "definition": {
                "name": {"en-US": content_name},
                "type": ACTIVITY_BASE + "/types/content",
            },
        },
        "context": _build_camara_context(
            school_id, device_id, platform_id,
            is_offline, server_id, tracking_depth,
        ),
    }
    return _emit(statement)


def emit_content_completed(
    student_id,
    school_id,
    device_id,
    platform_id,
    server_id,
    is_offline,
    content_id,
    content_name,
    duration_seconds,
    completion_status,
    tracking_depth="full",
):
    # Emits a content completed event
    # completion_status must be one of APPROVED_COMPLETION_STATUSES
    # Not available for click-only platforms -- record access only
    is_valid, error = validate_completion_status(completion_status)
    if not is_valid:
        _quarantine(
            {"content_id": content_id, "completion_status": completion_status},
            [error],
        )
        return False

    statement = {
        "id":        str(uuid.uuid4()),
        "timestamp": _now(),
        "actor":     _build_actor(student_id),
        "verb": {
            "id":      ADLNET_VERB_BASE + "/completed",
            "display": {"en-US": "completed"},
        },
        "object": {
            "id":         content_id,
            "objectType": "Activity",
            "definition": {
                "name": {"en-US": content_name},
                "type": ACTIVITY_BASE + "/types/content",
            },
        },
        "result": {
            "completion": completion_status == "Completed",
            "duration":   "PT" + str(duration_seconds) + "S",
            "extensions": {
                ACTIVITY_BASE + "/result/completion-status": completion_status,
            },
        },
        "context": _build_camara_context(
            school_id, device_id, platform_id,
            is_offline, server_id, tracking_depth,
        ),
    }
    return _emit(statement)


def emit_assessment_attempted(
    student_id,
    school_id,
    device_id,
    platform_id,
    server_id,
    is_offline,
    assessment_id,
    assessment_name,
    subject_id,
    attempt_number,
    score_raw,
    score_min,
    score_max,
    passed,
    completion_status,
    duration_seconds,
    tracking_depth="full",
):
    # Emits an assessment attempted event
    # subject_id matches fact_assessment_attempt.subject_id
    # attempt_number matches fact_assessment_attempt.attempt_number
    # Used in Score Improvement Rate formula in dbt Step 9
    # score_raw is NUMERIC(5,2) -- allows decimal scores like 87.50
    # completion_status must be one of APPROVED_COMPLETION_STATUSES
    is_valid, error = validate_completion_status(completion_status)
    if not is_valid:
        _quarantine(
            {"assessment_id": assessment_id, "completion_status": completion_status},
            [error],
        )
        return False

    scaled = round(score_raw / score_max, 4) if score_max > 0 else 0

    statement = {
        "id":        str(uuid.uuid4()),
        "timestamp": _now(),
        "actor":     _build_actor(student_id),
        "verb": {
            "id":      ADLNET_VERB_BASE + "/attempted",
            "display": {"en-US": "attempted"},
        },
        "object": {
            "id":         assessment_id,
            "objectType": "Activity",
            "definition": {
                "name": {"en-US": assessment_name},
                "type": ACTIVITY_BASE + "/types/assessment",
            },
        },
        "result": {
            "score": {
                "raw":    score_raw,
                "min":    score_min,
                "max":    score_max,
                "scaled": scaled,
            },
            "success":    passed,
            "completion": completion_status == "Completed",
            "duration":   "PT" + str(duration_seconds) + "S",
            "extensions": {
                ACTIVITY_BASE + "/result/completion-status": completion_status,
            },
        },
        "context": _build_camara_context(
            school_id, device_id, platform_id,
            is_offline, server_id, tracking_depth,
            extra={
                "subject_id":     subject_id,
                "attempt_number": attempt_number,
            },
        ),
    }
    return _emit(statement)


def emit_ai_interaction(
    student_id,
    school_id,
    device_id,
    platform_id,
    server_id,
    is_offline,
    ai_service_id,
    subject_id,
    query_type,
    duration_seconds,
    tracking_depth="full",
):
    # Emits an AI interaction event
    # query_type must be one of APPROVED_QUERY_TYPES:
    #   Clarification, Problem-solving, Guidance, Translation, Practice
    # subject_id matches fact_ai_usage.subject_id
    is_valid, error = validate_query_type(query_type)
    if not is_valid:
        _quarantine(
            {"ai_service_id": ai_service_id, "query_type": query_type},
            [error],
        )
        return False

    statement = {
        "id":        str(uuid.uuid4()),
        "timestamp": _now(),
        "actor":     _build_actor(student_id),
        "verb": {
            "id":      CAMARA_VERB_BASE + "/ai-queried",
            "display": {"en-US": "queried AI"},
        },
        "object": {
            "id":         ACTIVITY_BASE + "/ai/" + ai_service_id,
            "objectType": "Activity",
            "definition": {
                "type": ACTIVITY_BASE + "/types/ai-service",
            },
        },
        "result": {
            "duration": "PT" + str(duration_seconds) + "S",
        },
        "context": _build_camara_context(
            school_id, device_id, platform_id,
            is_offline, server_id, tracking_depth,
            extra={
                "subject_id": subject_id,
                "query_type": query_type,
            },
        ),
    }
    return _emit(statement)


def emit_game_event(
    student_id,
    school_id,
    device_id,
    platform_id,
    server_id,
    is_offline,
    game_id,
    game_name,
    event_type,
    tracking_depth="full",
    level=None,
    score=None,
    hint_used=False,
):
    # Emits a game event
    # event_type maps to a specific verb from the approved list
    # level is the game level number -- None if not applicable
    # score is the raw score -- None if not applicable
    # hint_used is True if the student requested a hint
    verb_map = {
        "launched":        ADLNET_VERB_BASE + "/launched",
        "exited":          ADLNET_VERB_BASE + "/exited",
        "level_started":   CAMARA_VERB_BASE + "/game-level-started",
        "level_completed": CAMARA_VERB_BASE + "/game-level-completed",
        "level_failed":    CAMARA_VERB_BASE + "/game-level-failed",
        "hint_requested":  CAMARA_VERB_BASE + "/hint-requested",
        "interacted":      ADLNET_VERB_BASE + "/interacted",
        "progressed":      ADLNET_VERB_BASE + "/progressed",
    }
    verb_id = verb_map.get(event_type, ADLNET_VERB_BASE + "/interacted")

    # Build result only if there is something to record
    result = {}
    if score is not None:
        result["score"] = {"raw": score}
    if hint_used:
        result["extensions"] = {
            ACTIVITY_BASE + "/result/hint-used": True,
        }

    # Build extra context fields
    extra = {}
    if level is not None:
        extra["level"] = level

    statement = {
        "id":        str(uuid.uuid4()),
        "timestamp": _now(),
        "actor":     _build_actor(student_id),
        "verb": {
            "id":      verb_id,
            "display": {"en-US": event_type.replace("_", " ")},
        },
        "object": {
            "id":         ACTIVITY_BASE + "/game/" + game_id,
            "objectType": "Activity",
            "definition": {
                "name": {"en-US": game_name},
                "type": ACTIVITY_BASE + "/types/game",
            },
        },
        "context": _build_camara_context(
            school_id, device_id, platform_id,
            is_offline, server_id, tracking_depth,
            extra=extra if extra else None,
        ),
    }
    if result:
        statement["result"] = result

    return _emit(statement)
