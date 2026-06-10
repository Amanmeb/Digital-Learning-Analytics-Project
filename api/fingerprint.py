# SHA-256 fingerprint calculator for deduplication
# Same formula used in xapi/validator.py on the edge
# Formula: SHA-256 of student_id|event_type|content_id|timestamp|school_id

import hashlib

CAMARA_CONTEXT_EXT = "https://camara.org/xapi/context"


def calculate_fingerprint(statement):
    # Calculates SHA-256 fingerprint from an xAPI statement dict
    # Returns empty string if calculation fails
    try:
        context = statement.get("context", {})
        extensions = context.get("extensions", {})
        camara_ext = extensions.get(CAMARA_CONTEXT_EXT, {})

        student_id = (
            statement
            .get("actor", {})
            .get("account", {})
            .get("name", "")
        )
        event_type = statement.get("verb", {}).get("id", "")
        content_id = statement.get("object", {}).get("id", "")
        timestamp = statement.get("timestamp", "")
        school_id = camara_ext.get("school_id", "")

        raw = (
            student_id + "|" +
            event_type + "|" +
            content_id + "|" +
            timestamp + "|" +
            school_id
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
    except Exception:
        return ""


def calculate_fingerprint_from_parts(
    student_id,
    event_type,
    content_id,
    timestamp,
    school_id,
):
    # Calculates fingerprint directly from individual fields
    # Used by manual import routes
    try:
        raw = (
            str(student_id) + "|" +
            str(event_type) + "|" +
            str(content_id) + "|" +
            str(timestamp) + "|" +
            str(school_id)
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
    except Exception:
        return ""
