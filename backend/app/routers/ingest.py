import logging
import json
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas import (
    FactAiUsageIn,
    FactAssessmentAttemptIn,
    FactContentUsageIn,
    FactSessionIn,
    FactTeacherSessionIn,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ingest"])


async def _quarantine(
    db: AsyncSession,
    payload: dict,
    reason: str,
    request_id: str | None = None,
):
    try:
        await db.execute(
            text("""
                INSERT INTO ops.system_log
                (log_level, component, event, request_id, details)
                VALUES
                ('ERROR', 'ingest', 'quarantine', :request_id, :details)
            """),
            {
                "request_id": request_id,
                "details": json.dumps({
                    "payload": payload,
                    "reason": reason,
                }),
            },
        )
        await db.commit()

    except Exception:
        await db.rollback()
        logger.exception("quarantine insert failed")


async def _ingest_fact(
    db: AsyncSession,
    mart_table: str,
    pk_col: str,
    pk_value: str,
    payload: dict[str, Any],
    insert_sql: str,
    insert_params: dict[str, Any],
) -> JSONResponse:
    """Shared duplicate-check + insert + error-handling path for fact tables.

    mart_table and pk_col are hardcoded by each caller, not user-supplied,
    so the f-string in the SELECT is safe from injection.
    """
    result = await db.execute(
        text(f"SELECT 1 FROM {mart_table} WHERE {pk_col} = :pk"),  # noqa: S608
        {"pk": pk_value},
    )
    if result.scalar():
        return JSONResponse(
            status_code=200,
            content={"status": "duplicate", pk_col: pk_value},
        )
    try:
        await db.execute(text(insert_sql), insert_params)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        await _quarantine(db, mart_table, payload, f"db_error: {exc}")
        return JSONResponse(
            status_code=200,
            content={"status": "quarantined", "reason": "db_error"},
        )
    return JSONResponse(
        status_code=201,
        content={"status": "accepted", pk_col: pk_value},
    )


@router.post("/ingest/sessions")
async def ingest_session(
    payload: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
):
    request_id = str(uuid4())

    logger.info(
        "ingest_session received",
        extra={"request_id": request_id},
    )

    # -------------------------
    # Validation layer
    # -------------------------
    try:
        record = FactSessionIn(**payload)

    except ValidationError as exc:
        logger.warning(
            "validation_failed",
            extra={
                "request_id": request_id,
                "error": exc.errors(),
            },
        )

        await _quarantine(
            db,
            payload,
            reason="validation_failed",
            request_id=request_id,
        )

        return JSONResponse(
            status_code=200,
            content={
                "status": "quarantined",
                "reason": "validation_failed",
                "request_id": request_id,
            },
        )

    # -------------------------
    # DB insert layer
    # -------------------------
    try:
        await db.execute(
            text("""
                INSERT INTO mart.fact_session
                (
                    session_id,
                    student_id,
                    school_id,
                    device_id,
                    platform_id,
                    date_key,
                    project_id,
                    session_duration_minutes,
                    is_offline
                )
                VALUES
                (
                    :session_id,
                    :student_id,
                    :school_id,
                    :device_id,
                    :platform_id,
                    :date_key,
                    :project_id,
                    :duration,
                    :offline
                )
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

        logger.info(
            "fact_session_insert_success",
            extra={
                "request_id": request_id,
                "session_id": record.session_id,
            },
        )

<<<<<<< Updated upstream
    return JSONResponse(
        status_code=201,
        content={"status": "accepted", "session_id": record.session_id},
    )


@router.post("/ingest/teacher-sessions")
async def ingest_teacher_session(
    payload: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    try:
        record = FactTeacherSessionIn(**payload)
    except ValidationError as exc:
        await _quarantine(db, "fact_teacher_session", payload, str(exc))
        return JSONResponse(
            status_code=200,
            content={"status": "quarantined", "reason": "validation_failed"},
        )
    return await _ingest_fact(
        db,
        mart_table="mart.fact_teacher_session",
        pk_col="teacher_session_id",
        pk_value=record.teacher_session_id,
        payload=payload,
        insert_sql=(
            "INSERT INTO mart.fact_teacher_session"
            " (teacher_session_id, teacher_id, school_id, device_id, platform_id,"
            "  date_key, session_duration_minutes, is_offline)"
            " VALUES (:tid, :teacher_id, :school_id, :device_id, :platform_id,"
            "         :date_key, :duration, :offline)"
        ),
        insert_params={
            "tid": record.teacher_session_id,
            "teacher_id": record.teacher_id,
            "school_id": record.school_id,
            "device_id": record.device_id,
            "platform_id": record.platform_id,
            "date_key": record.date_id,
            "duration": record.session_duration_minutes,
            "offline": record.is_offline,
        },
    )


@router.post("/ingest/content-usage")
async def ingest_content_usage(
    payload: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    try:
        record = FactContentUsageIn(**payload)
    except ValidationError as exc:
        await _quarantine(db, "fact_content_usage", payload, str(exc))
        return JSONResponse(
            status_code=200,
            content={"status": "quarantined", "reason": "validation_failed"},
        )
    return await _ingest_fact(
        db,
        mart_table="mart.fact_content_usage",
        pk_col="content_usage_id",
        pk_value=record.content_usage_id,
        payload=payload,
        insert_sql=(
            "INSERT INTO mart.fact_content_usage"
            " (content_usage_id, session_id, content_id, platform_id,"
            "  date_key, time_spent_minutes, completion_status)"
            " VALUES (:cuid, :session_id, :content_id, :platform_id,"
            "         :date_key, :time_spent, :completion)"
        ),
        insert_params={
            "cuid": record.content_usage_id,
            "session_id": record.session_id,
            "content_id": record.content_id,
            "platform_id": record.platform_id,
            "date_key": record.date_id,
            "time_spent": record.time_spent_minutes,
            "completion": record.completion_status,
        },
    )


@router.post("/ingest/ai-usage")
async def ingest_ai_usage(
    payload: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    try:
        record = FactAiUsageIn(**payload)
    except ValidationError as exc:
        await _quarantine(db, "fact_ai_usage", payload, str(exc))
        return JSONResponse(
            status_code=200,
            content={"status": "quarantined", "reason": "validation_failed"},
        )
    return await _ingest_fact(
        db,
        mart_table="mart.fact_ai_usage",
        pk_col="ai_usage_id",
        pk_value=record.ai_usage_id,
        payload=payload,
        insert_sql=(
            "INSERT INTO mart.fact_ai_usage"
            " (ai_usage_id, session_id, ai_service_id, subject_id,"
            "  date_key, query_count, time_spent_minutes, query_type)"
            " VALUES (:auid, :session_id, :ai_service_id, :subject_id,"
            "         :date_key, :query_count, :time_spent, :query_type)"
        ),
        insert_params={
            "auid": record.ai_usage_id,
            "session_id": record.session_id,
            "ai_service_id": record.ai_service_id,
            "subject_id": record.subject_id,
            "date_key": record.date_id,
            "query_count": record.query_count,
            "time_spent": record.time_spent_minutes,
            "query_type": record.query_type,
        },
    )


@router.post("/ingest/assessment-attempts")
async def ingest_assessment_attempt(
    payload: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    try:
        record = FactAssessmentAttemptIn(**payload)
    except ValidationError as exc:
        await _quarantine(db, "fact_assessment_attempt", payload, str(exc))
        return JSONResponse(
            status_code=200,
            content={"status": "quarantined", "reason": "validation_failed"},
        )
    return await _ingest_fact(
        db,
        mart_table="mart.fact_assessment_attempt",
        pk_col="attempt_id",
        pk_value=record.assessment_attempt_id,
        payload=payload,
        insert_sql=(
            "INSERT INTO mart.fact_assessment_attempt"
            " (attempt_id, student_id, content_id, date_key, score, completion_status)"
            " VALUES (:aid, :student_id, :content_id, :date_key, :score, :completion)"
        ),
        insert_params={
            "aid": record.assessment_attempt_id,
            "student_id": record.student_id,
            "content_id": record.content_id,
            "date_key": record.date_id,
            "score": record.score,
            "completion": record.completion_status,
        },
    )
=======
        return {
            "status": "inserted",
            "session_id": record.session_id,
            "request_id": request_id,
        }

    except Exception as exc:
        await db.rollback()

        logger.exception(
            "fact_session_insert_failed",
            extra={
                "request_id": request_id,
                "session_id": getattr(record, "session_id", None),
            },
        )

        await _quarantine(
            db,
            payload,
            reason=f"db_error: {str(exc)}",
            request_id=request_id,
        )

        return JSONResponse(
            status_code=200,
            content={
                "status": "quarantined",
                "reason": "db_error",
                "request_id": request_id,
            },
        )

        # logger.error("DB insert failed", exc_info=True)

        # logger.exception(
        #     "fact_session insert failed",
        #     extra={"payload": payload},
        # )

        # try:
        #     await _quarantine(
        #         db,
        #         payload,
        #         f"db_error: {str(exc)}"
        #     )
        # except Exception:
        #     logger.exception("quarantine insert failed")

        # return JSONResponse(
        #     status_code=200,
        #     content={
        #         "status": "quarantined",
        #         "reason": "db_error",
        #     },
        # )
    
# import logging
# logger = logging.getLogger(__name__)
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


# async def _quarantine(db: AsyncSession, payload: dict, reason: str):
#     try:
#         await db.execute(
#             text("""
#                 INSERT INTO ops.system_log (log_level, component, event, details)
#                 VALUES ('ERROR', 'ingest', 'quarantine', :details)
#             """),
#             {"details": json.dumps({"payload": payload, "reason": reason})},
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
#         await _quarantine(db, payload, str(exc))
#         return {"status": "quarantined", "reason": "validation_failed"}

#     try:
#         await db.execute(
#             logger.info(
#     "fact_session ingest attempt",
#     extra={
#         "session_id": record.session_id,
#         "platform_id": record.platform_id,
#         "date_id": record.date_id,
#     },
# )
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

#         return {"status": "inserted", "session_id": record.session_id}

#     # except Exception as exc:
#     #     await db.rollback()
#     #     await _quarantine(db, payload, f"db_error: {str(exc)}")
#     #     return {"status": "quarantined", "reason": "db_error"}
#     # except Exception as exc:
#     #     await db.rollback()
#     #     logger.exception("FACT_SESSION INSERT FAILED")  # <-- add this
#     #     await _quarantine(db, "fact_session", payload, f"db_error: {exc}")
#     #     return {"status": "quarantined", "reason": "db_error"}
    
#     except Exception as exc:
#         await db.rollback()

#         logger.exception(
#             logger.error("DB insert failed", exc_info=True)
#             "fact_session insert failed",
#             extra={"payload": payload}
#     )

#     try:
#         await _quarantine(db, payload, f"db_error: {exc}")
#     except Exception:
#         logger.exception("quarantine insert failed")

#     return JSONResponse(
#         status_code=200,
#         content={"status": "quarantined", "reason": "db_error"}
#     )
>>>>>>> Stashed changes
