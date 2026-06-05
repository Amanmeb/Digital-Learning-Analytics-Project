
import hashlib



APPROVED_VERBS = [
    # ADL standard verbs
    "http://adlnet.gov/expapi/verbs/launched",
    "http://adlnet.gov/expapi/verbs/exited",
    "http://adlnet.gov/expapi/verbs/experienced",
    "http://adlnet.gov/expapi/verbs/attempted",
    "http://adlnet.gov/expapi/verbs/completed",
    "http://adlnet.gov/expapi/verbs/passed",
    "http://adlnet.gov/expapi/verbs/failed",
    "http://adlnet.gov/expapi/verbs/answered",
    "http://adlnet.gov/expapi/verbs/interacted",
    "http://adlnet.gov/expapi/verbs/progressed",
    # TinCan verbs
    "http://id.tincanapi.com/verb/skipped",
    "http://id.tincanapi.com/verb/viewed",
    # ADL login verbs
    "https://w3id.org/xapi/adl/verbs/logged-in",
    "https://w3id.org/xapi/adl/verbs/logged-out",
    # Camara custom verbs
    "https://camara.org/xapi/verbs/session-started",
    "https://camara.org/xapi/verbs/session-ended",
    "https://camara.org/xapi/verbs/ai-queried",
    "https://camara.org/xapi/verbs/game-level-started",
    "https://camara.org/xapi/verbs/game-level-completed",
    "https://camara.org/xapi/verbs/game-level-failed",
    "https://camara.org/xapi/verbs/hint-requested",
]


APPROVED_QUERY_TYPES = [
    "Clarification",
    "Problem-solving",
    "Guidance",
    "Translation",
    "Practice",
]


APPROVED_COMPLETION_STATUSES = [
    "Completed",
    "Incomplete",
    "Passed",
    "Failed",
    "Unknown",
]


APPROVED_TRACKING_DEPTHS = [
    "full",
    "partial",
    "click_only",
]


REQUIRED_CAMARA_CONTEXT_FIELDS = [
    "school_id",
    "device_id",
    "platform_id",
    "is_offline",
    "server_id",
    "tracking_depth",
]

# Camara context extension URL
CAMARA_CONTEXT_EXT = "https://camara.org/xapi/context"


def validate_statement(statement):
    # Returns (is_valid, list_of_errors)
    # Empty error list means statement is valid
    # Called by emitter before writing to SQLite queue
    # Called again by FastAPI before writing to PostgreSQL
    errors = []

    # Check actor exists and has correct structure
    if "actor" not in statement:
        errors.append("Missing required field: actor")
    else:
        actor = statement["actor"]
        if "account" not in actor and "mbox" not in actor:
            errors.append("Actor must have account or mbox")
        if "account" in actor:
            if "name" not in actor["account"]:
                errors.append("Actor account missing name")
            if "homePage" not in actor["account"]:
                errors.append("Actor account missing homePage")

    # Check verb exists and is in approved list
    if "verb" not in statement:
        errors.append("Missing required field: verb")
    else:
        verb = statement["verb"]
        if "id" not in verb:
            errors.append("Verb missing id")
        elif verb["id"] not in APPROVED_VERBS:
            errors.append("Verb not in approved list: " + verb["id"])

    # Check object exists and has id
    if "object" not in statement:
        errors.append("Missing required field: object")
    else:
        if "id" not in statement["object"]:
            errors.append("Object missing id")

    # Check timestamp exists and is valid ISO 8601
    if "timestamp" not in statement:
        errors.append("Missing required field: timestamp")
    else:
        ts = statement["timestamp"]
        if not isinstance(ts, str) or len(ts) < 19:
            errors.append("Timestamp format invalid: use ISO 8601")

    # Check all required Camara context fields exist
    context = statement.get("context", {})
    extensions = context.get("extensions", {})
    camara_ext = extensions.get(CAMARA_CONTEXT_EXT, {})

    for field in REQUIRED_CAMARA_CONTEXT_FIELDS:
        if field not in camara_ext:
            errors.append("Missing Camara context field: " + field)

    # Check tracking_depth is valid if present
    tracking_depth = camara_ext.get("tracking_depth", "")
    if tracking_depth and tracking_depth not in APPROVED_TRACKING_DEPTHS:
        errors.append("Invalid tracking_depth: " + tracking_depth)

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_completion_status(status):
    # Returns (is_valid, error_message)
    # Used by emitter functions that record completion
    if status not in APPROVED_COMPLETION_STATUSES:
        return False, "Completion status not in approved list: " + status
    return True, ""


def validate_query_type(query_type):
    # Returns (is_valid, error_message)
    # Used by emit_ai_interaction
    if query_type not in APPROVED_QUERY_TYPES:
        return False, "Query type not in approved list: " + query_type
    return True, ""


def calculate_fingerprint(statement):

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
