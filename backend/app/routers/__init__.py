from .dashboard import router as dashboard_router
from .ingest import router as ingest_router

__all__ = [
    "dashboard_router",
    "ingest_router",
]





# import json
# from typing import Any

# from fastapi import APIRouter, Body, Depends
# from fastapi.responses import JSONResponse
# from pydantic import ValidationError
# from sqlalchemy import text
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.database import get_db
# from app.models.schemas import FactSessionIn

# router = APIRouter(tags=["ingest"])


# async def _quarantine(
#     db: AsyncSession,
#     table_name: str,
#     payload: dict[str, Any],
#     reason: str,
# ) -> None:
#     try:
#         await db.execute(
#             text(
#                 "INSERT INTO raw.quarantine (table_name, raw_payload, rejection_reason)"
#                 " VALUES (:t, :p::jsonb, :r)"
#             ),
#             {"t": table_name, "p": json.dumps(payload), "r": reason},
#         )
#         await db.commit()
#     except Exception:
#         await db.rollback()


# @router.post("/ingest/sessions")
# async def ingest_session(
#     payload: dict[str, Any] = Body(...),
#     db: AsyncSession = Depends(get_db),
# ) -> JSONResponse:
#     try:
#         record = FactSessionIn(**payload)
#     except ValidationError as exc:
#         await _quarantine(db, "fact_session", payload, str(exc))
#         return JSONResponse(
#             status_code=200,
#             content={"status": "quarantined", "reason": "validation_failed"},
#         )

#     result = await db.execute(
#         text("SELECT 1 FROM mart.fact_session WHERE session_id = :sid"),
#         {"sid": record.session_id},
#     )
#     if result.scalar():
#         return JSONResponse(
#             status_code=200,
#             content={"status": "duplicate", "session_id": record.session_id},
#         )

#     try:
#         await db.execute(
#             text(
#                 "INSERT INTO mart.fact_session"
#                 " (session_id, student_id, school_id, device_id, platform_id,"
#                 "  date_key, project_id, session_duration_minutes, is_offline)"
#                 " VALUES (:session_id, :student_id, :school_id, :device_id, :platform_id,"
#                 "         :date_key, :project_id, :duration, :offline)"
#             ),
#             {
#                 "session_id": record.session_id,
#                 "student_id": record.student_id,
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
#     except Exception as exc:
#         await db.rollback()
#         await _quarantine(db, "fact_session", payload, f"db_error: {exc}")
#         return JSONResponse(
#             status_code=200,
#             content={"status": "quarantined", "reason": "db_error"},
#         )

#     return JSONResponse(
#         status_code=201,
#         content={"status": "accepted", "session_id": record.session_id},
#     )
