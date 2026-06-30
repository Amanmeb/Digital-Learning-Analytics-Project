import hashlib
import json
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import XAPIStatementIn


def compute_fingerprint(statement: dict) -> str:
    """
    Stable SHA256 fingerprint used for idempotency.
    """
    canonical = json.dumps(statement, sort_keys=True, default=str)

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


def normalize(statement: XAPIStatementIn) -> dict:
    """
    Pydantic v2 compatible conversion.
    """
    if hasattr(statement, "model_dump"):
        return statement.model_dump()

    return dict(statement)


async def ingest_xapi_statement(
    payload: XAPIStatementIn,
    db: AsyncSession,
) -> dict:

    statement = normalize(payload)

    fingerprint = compute_fingerprint(statement)

    await db.execute(
        text(
            """
            INSERT INTO raw.xapi_statements
            (
                statement_id,
                server_id,
                school_id,
                actor,
                verb,
                object,
                result,
                context,
                timestamp,
                event_fingerprint,
                processed
            )
            VALUES
            (
                :statement_id,
                :server_id,
                :school_id,
                CAST(:actor AS jsonb),
                CAST(:verb AS jsonb),
                CAST(:object AS jsonb),
                CAST(:result AS jsonb),
                CAST(:context AS jsonb),
                :timestamp,
                :fingerprint,
                FALSE
            )
            ON CONFLICT (statement_id)
            DO NOTHING
            """
        ),
        {
            "statement_id": statement["statement_id"],
            "server_id": statement["server_id"],
            "school_id": statement["school_id"],
            "actor": json.dumps(statement["actor"]),
            "verb": json.dumps(statement["verb"]),
            "object": json.dumps(statement["object"]),
            "result": json.dumps(statement.get("result", {})),
            "context": json.dumps(statement.get("context", {})),
            "timestamp": statement.get(
                "timestamp",
                datetime.utcnow(),
            ),
            "fingerprint": fingerprint,
        },
    )

    await db.commit()

    return {
        "statement_id": statement["statement_id"],
        "fingerprint": fingerprint,
        "status": "ingested_raw",
    }

# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import text
# from datetime import datetime
# import json
# import hashlib

# from app.models.schemas import FactSessionIn


# # -----------------------------
# # Fingerprint (idempotency key)
# # -----------------------------
# def compute_fingerprint(payload: dict) -> str:
#     canonical = json.dumps(payload, sort_keys=True, default=str)
#     return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# # -----------------------------
# # Normalize Pydantic → dict
# # -----------------------------
# def normalize_payload(payload: FactSessionIn) -> dict:
#     # Pydantic v2 safe
#     if hasattr(payload, "model_dump"):
#         return payload.model_dump()
#     return dict(payload)


# # -----------------------------
# # RAW ingestion (ONLY WRITE PATH)
# # -----------------------------
# async def ingest_session(payload: FactSessionIn, db: AsyncSession) -> dict:
#     event = normalize_payload(payload)

#     fingerprint = compute_fingerprint(event)

#     # ensure required fields exist
#     statement_id = event.get("session_id")
#     if not statement_id:
#         raise ValueError("session_id is required")

#     await db.execute(
#         text("""
#             INSERT INTO raw.xapi_statements (
#                 statement_id,
#                 server_id,
#                 school_id,
#                 actor,
#                 verb,
#                 object,
#                 result,
#                 context,
#                 timestamp,
#                 event_fingerprint,
#                 processed
#             )
#             VALUES (
#                 :statement_id,
#                 :server_id,
#                 :school_id,
#                 :actor,
#                 :verb,
#                 :object,
#                 :result,
#                 :context,
#                 :timestamp,
#                 :event_fingerprint,
#                 FALSE
#             )
#             ON CONFLICT (statement_id)
#             DO NOTHING
#         """),
#         {
#             "statement_id": statement_id,
#             "server_id": event.get("server_id", "unknown"),
#             "school_id": event.get("school_id"),
#             "actor": json.dumps(event.get("actor")),
#             "verb": json.dumps(event.get("verb")),
#             "object": json.dumps(event.get("object")),
#             "result": json.dumps(event.get("result")),
#             "context": json.dumps(event.get("context")),
#             "timestamp": event.get("timestamp") or datetime.utcnow(),
#             "event_fingerprint": fingerprint,
            
#         },
#     )

#     await db.commit()

#     return {
#         "session_id": statement_id,
#         "fingerprint": fingerprint,
#         "status": "ingested_raw"
#     }

# modified to push ingestion into mart
# from sqlalchemy import text
# from sqlalchemy.exc import IntegrityError


# async def ingest_session(payload: dict, db):

#     try:
#         await db.execute(
#             text("""
#                 INSERT INTO mart.fact_session
#                 (
#                     session_id,
#                     student_id,
#                     school_id,
#                     device_id,
#                     platform_id,
#                     date_key,
#                     project_id,
#                     session_duration_minutes,
#                     is_offline
#                 )
#                 VALUES
#                 (
#                     :session_id,
#                     :student_id,
#                     :school_id,
#                     :device_id,
#                     :platform_id,
#                     :date_key,
#                     :project_id,
#                     :duration,
#                     :offline
#                 )
#             """),
#             {
#                 "session_id": payload["session_id"],
#                 "student_id": payload["student_id"],
#                 "school_id": payload["school_id"],
#                 "device_id": payload["device_id"],
#                 "platform_id": payload["platform_id"],
#                 "date_key": payload["date_id"],
#                 "project_id": payload["project_id"],
#                 "duration": payload["session_duration_minutes"],
#                 "offline": payload["is_offline"],
#             },
#         )

#         await db.commit()

#         return {
#             "status": "success",
#             "session_id": payload["session_id"]
#         }

#     except IntegrityError as e:
#         await db.rollback()

#         return {
#             "status": "error",
#             "reason": "constraint_violation",
#             "detail": str(e.orig)
#         }

#     except Exception as e:
#         await db.rollback()

#         return {
#             "status": "error",
#             "reason": "internal_error",
#             "detail": str(e)
#         }

# old codes
# from sqlalchemy import text
# from sqlalchemy.exc import IntegrityError

# from app.models.fact_session import FactSession
# from app.services.exceptions import (
#     NotFoundError,
#     DuplicateError,
# )


# async def ingest_session(payload, db):

#     # ----------------------------------
#     # Duplicate session check
#     # ----------------------------------

#     existing = await db.execute(
#         text("""
#             SELECT 1
#             FROM mart.fact_session
#             WHERE session_id = :session_id
#         """),
#         {"session_id": payload.session_id},
#     )

#     if existing.scalar():
#         raise DuplicateError(
#             f"Session {payload.session_id} already exists"
#         )

#     # ----------------------------------
#     # Dimension existence checks
#     # ----------------------------------

#     dimensions = [
#         ("student", "mart.dim_student", "student_id", payload.student_id),
#         ("school", "mart.dim_school", "school_id", payload.school_id),
#         ("device", "mart.dim_device", "device_id", payload.device_id),
#         ("platform", "mart.dim_platform", "platform_id", payload.platform_id),
#         ("project", "mart.dim_project", "project_id", payload.project_id),
#         ("date", "mart.dim_date", "date_key", payload.date_id),
#     ]

#     for name, table, column, value in dimensions:

#         result = await db.execute(
#             text(f"""
#                 SELECT 1
#                 FROM {table}
#                 WHERE {column} = :value
#             """),
#             {"value": value},
#         )

#         if not result.scalar():
#             raise NotFoundError(
#                 f"{name} '{value}' not found"
#             )

#     # ----------------------------------
#     # Create session
#     # ----------------------------------

#     session = FactSession(
#         session_id=payload.session_id,
#         student_id=payload.student_id,
#         school_id=payload.school_id,
#         device_id=payload.device_id,
#         platform_id=payload.platform_id,
#         date_key=payload.date_id,
#         project_id=payload.project_id,
#         session_duration_minutes=payload.session_duration_minutes,
#         is_offline=payload.is_offline,
#     )

#     try:

#         db.add(session)

#         await db.commit()

#         await db.refresh(session)

#         return session

#     except IntegrityError as e:

#         await db.rollback()

#         if "fact_session_pkey" in str(e):
#             raise DuplicateError(
#                 f"Session {payload.session_id} already exists"
#             )

#         raise