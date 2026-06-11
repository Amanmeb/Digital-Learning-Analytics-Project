import logging
logger = logging.getLogger(__name__)
import json
from typing import Any

from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas import FactSessionIn

router = APIRouter(tags=["ingest"])


async def _quarantine(db: AsyncSession, payload: dict, reason: str):
    try:
        await db.execute(
            text("""
                INSERT INTO ops.system_log (log_level, component, event, details)
                VALUES ('ERROR', 'ingest', 'quarantine', :details)
            """),
            {"details": json.dumps({"payload": payload, "reason": reason})},
        )
        await db.commit()
    except Exception:
        await db.rollback()


@router.post("/ingest/sessions")
async def ingest_session(
    payload: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:

    try:
        record = FactSessionIn(**payload)
    except ValidationError as exc:
        await _quarantine(db, payload, str(exc))
        return {"status": "quarantined", "reason": "validation_failed"}

    try:
        await db.execute(
            text("""
                INSERT INTO mart.fact_session
                (session_id, student_id, school_id, device_id, platform_id,
                 date_key, project_id, session_duration_minutes, is_offline)
                VALUES
                (:session_id, :student_id, :school_id, :device_id, :platform_id,
                 :date_key, :project_id, :duration, :offline)
            """),
            {
                "session_id": record.session_id,
                "student_id": record.student_id,
                "school_id": record.school_id,
                "device_id": record.device_id,
                "platform_id": record.platform_id,
                "date_key": record.date_id,
                "project_id": record.project_id,
                "duration": record.session_duration_minutes,
                "offline": record.is_offline,
            },
        )
        await db.commit()

        return {"status": "inserted", "session_id": record.session_id}

    # except Exception as exc:
    #     await db.rollback()
    #     await _quarantine(db, payload, f"db_error: {str(exc)}")
    #     return {"status": "quarantined", "reason": "db_error"}
    # except Exception as exc:
    #     await db.rollback()
    #     logger.exception("FACT_SESSION INSERT FAILED")  # <-- add this
    #     await _quarantine(db, "fact_session", payload, f"db_error: {exc}")
    #     return {"status": "quarantined", "reason": "db_error"}
    
    except Exception as exc:
        await db.rollback()
        logger.exception("fact_session insert failed")

    await _quarantine(db, payload, f"db_error: {str(exc)}")

    return JSONResponse(
        status_code=200,
        content={"status": "quarantined", "reason": "db_error"},
    )

		


