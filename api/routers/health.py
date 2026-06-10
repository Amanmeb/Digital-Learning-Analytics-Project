# Health check endpoints
# Used by monitoring tools and the school status monitor

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from api.database import get_db, check_db_connection

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db=Depends(get_db)):
    # Returns overall system health status
    db_ok = check_db_connection()
    return {
        "status":   "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "version":  "1.0.0",
    }


@router.get("/ping")
def ping():
    # Simple liveness check -- no database required
    return {"status": "ok"}


@router.get("/sync-status/{school_id}")
def sync_status(school_id, db=Depends(get_db)):
    # Returns sync status for a specific school
    try:
        result = db.execute(
            text("""
                SELECT
                    school_id,
                    status,
                    synced_at,
                    statements_received,
                    statements_inserted,
                    statements_duplicate,
                    statements_rejected,
                    error_message
                FROM ops.sync_log
                WHERE school_id = :school_id
                ORDER BY synced_at DESC
                LIMIT 1
            """),
            {"school_id": school_id}
        ).fetchone()

        if not result:
            return {
                "school_id":  school_id,
                "status":     "no_sync_found",
                "last_sync":  None,
            }

        return {
            "school_id":             result.school_id,
            "status":                result.status,
            "last_sync":             str(result.synced_at),
            "statements_received":   result.statements_received,
            "statements_inserted":   result.statements_inserted,
            "statements_duplicate":  result.statements_duplicate,
            "statements_rejected":   result.statements_rejected,
            "error_message":         result.error_message,
        }
    except Exception as e:
        return {"school_id": school_id, "status": "error", "detail": str(e)}
