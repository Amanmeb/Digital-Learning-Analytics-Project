from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


async def ingest_session(payload: dict, db):

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
                "session_id": payload["session_id"],
                "student_id": payload["student_id"],
                "school_id": payload["school_id"],
                "device_id": payload["device_id"],
                "platform_id": payload["platform_id"],
                "date_key": payload["date_id"],
                "project_id": payload["project_id"],
                "duration": payload["session_duration_minutes"],
                "offline": payload["is_offline"],
            },
        )

        await db.commit()

        return {
            "status": "success",
            "session_id": payload["session_id"]
        }

    except IntegrityError as e:
        await db.rollback()

        return {
            "status": "error",
            "reason": "constraint_violation",
            "detail": str(e.orig)
        }

    except Exception as e:
        await db.rollback()

        return {
            "status": "error",
            "reason": "internal_error",
            "detail": str(e)
        }
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