import logging

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from app.database import get_db
from app.models.schemas import FactSessionIn
from app.services.ingestion import ingest_session
from app.services.exceptions import (
    NotFoundError,
    DuplicateError,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ingest"])


@router.post(
    "/sessions",
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    payload: FactSessionIn,
    db=Depends(get_db),
):
    try:
        session = await ingest_session(payload, db)

        return {
            "status": "success",
            "message": "Session created",
            "data": {
                "session_id": session.session_id,
            },
        }

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except DuplicateError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    except Exception:
        logger.exception("session_ingest_failed")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
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

