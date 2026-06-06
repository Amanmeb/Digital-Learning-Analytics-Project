# Standard error codes for the CDLAID ingestion API
# All API responses use these codes for consistent error handling
# E001 to E014 are business logic errors
# E099 is a catch-all for internal server errors

from fastapi import HTTPException

ERROR_CODES = {
    "E001": "Invalid API key",
    "E002": "Invalid server ID",
    "E003": "School not registered",
    "E004": "Malformed xAPI statement",
    "E005": "Missing required field",
    "E006": "Duplicate statement rejected",
    "E007": "Score out of range",
    "E008": "Student ID not found",
    "E009": "Content ID not found",
    "E010": "Timestamp format invalid",
    "E011": "Batch size exceeds limit",
    "E012": "File format not supported",
    "E013": "File too large",
    "E014": "Import validation failed",
    "E099": "Internal server error",
}


def api_error(code, detail=None, status_code=400):
    # Raises a standard API error with the given error code
    message = ERROR_CODES.get(code, "Unknown error")
    if detail:
        message = message + ": " + detail
    raise HTTPException(
        status_code=status_code,
        detail={"error_code": code, "message": message},
    )
