import logging
logger = logging.getLogger(__name__)
import json
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas import FactSessionIn
from app.auth.deps import get_current_user
from app.auth.device import validate_device
from app.models import DimStudent, DimDevice, DimProject, DimSchool, DimDate
from app.models import FactSession




router = APIRouter(tags=["ingest"])


async def assert_exists(db, model, field, value, name: str):
    stmt = select(model).where(field == value)
    result = await db.execute(stmt)
    obj = result.scalar_one_or_none()

    if not obj:
        raise HTTPException(
            status_code=400,
            detail=f"{name} does not exist: {value}"
        )
    return obj



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

async def ingest_session(payload: dict, db: AsyncSession = Depends(get_db)):
    try:
        # 1. validate dimensions FIRST (prevents FK crashes)
        await assert_exists(db, DimStudent, DimStudent.student_id, payload["student_id"], "Student")
        await assert_exists(db, DimSchool, DimSchool.school_id, payload["school_id"], "School")
        await assert_exists(db, DimDevice, DimDevice.device_id, payload["device_id"], "Device")
        await assert_exists(db, DimProject, DimProject.project_id, payload["project_id"], "Project")
        await assert_exists(db, DimDate, DimDate.date_key, payload["date_id"], "Date")

        # 2. insert fact
        session = FactSession(
            session_id=payload["session_id"],
            student_id=payload["student_id"],
            school_id=payload["school_id"],
            device_id=payload["device_id"],
            platform_id=payload["platform_id"],
            date_key=payload["date_id"],
            project_id=payload["project_id"],
            session_duration_minutes=payload["session_duration_minutes"],
            is_offline=payload["is_offline"],
        )

        db.add(session)
        await db.commit()

        return {"status": "success", "session_id": payload["session_id"]}

    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()
        return {
            "status": "error",
            "reason": "db_error",
            "detail": str(e)
        }


# @router.post("/ingest/sessions")
# async def ingest_session(
#     payload: dict[str, Any] = Body(...),
#     db: AsyncSession = Depends(get_db),
#     user: dict = Depends(get_current_user),
# ):

#     try:
#         record = FactSessionIn(**payload)

#     except ValidationError as exc:
#         await _quarantine(db, payload, str(exc))
#         return {"status": "quarantined", "reason": "validation_failed"}

#     # -------------------------
#     # DEVICE VALIDATION (correct)
#     # -------------------------
#     await validate_device(
#         db,
#         user_id=user["user_id"],
#         device_id=record.device_id,
#     )

#     try:
#         await db.execute(
#             text("""
#                 INSERT INTO mart.fact_session
#                 (session_id, student_id, school_id, device_id, platform_id,
#                  date_key, project_id, session_duration_minutes, is_offline)
#                 VALUES
#                 (:session_id, :student_id, :school_id, :device_id, :platform_id,
#                  :date_key, :project_id, :duration, :offline)
#             """),
#             {
#                 "session_id": record.session_id,
#                 "student_id": user["user_id"],
#                 "school_id": record.school_id,
#                 "device_id": record.device_id,
#                 "platform_id": record.platform_id,
#                 "date_key": record.date_id,
#                 "project_id": record.project_id,
#                 "duration": record.session_duration_minutes,
#                 "offline": record.is_offline,
#             },
#         )

#         await db.commit()
#         return {"status": "inserted", "session_id": record.session_id}

#     except Exception as exc:
#         await db.rollback()

#         logger.exception("fact_session insert failed")

#         await _quarantine(
#             db,
#             payload,
#             f"db_error: {str(exc)}",
#         )

        # return JSONResponse(
        #     status_code=500,
        #     content={
        #         "status": "quarantined",
        #         "reason": "db_error",
        #     },
        # )
		


