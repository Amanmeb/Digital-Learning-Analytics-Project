from fastapi import APIRouter, Depends, HTTPException, status


from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas import XAPIStatementIn
from app.services.ingestion import ingest_xapi_statement

# logger = logging.getLogger(__name__)

router = APIRouter(tags=["Ingestion"])


@router.post(
    "/ingest/xapi",
    status_code=status.HTTP_201_CREATED,
)
async def ingest_xapi(
    payload: XAPIStatementIn,
    db: AsyncSession = Depends(get_db),
):
  

    try:

        result = await ingest_xapi_statement(payload, db)

        return {
            "status": "accepted",
            "statement_id": result["statement_id"],
        }
    

    except Exception:

        raise HTTPException(
            status_code=500,
            detail="Failed to ingest xAPI statement",
        )

# @router.post(
#     "/sessions",
#     status_code=status.HTTP_201_CREATED,
# )
# async def create_session(
#     payload: FactSessionIn,
#     db=Depends(get_db),
# ):
#     try:
#         session = await ingest_session(payload, db)

#         return {
#             "status": "success",
#             "message": "Session created",
#             "data": {
#                 "session_id": session.session_id,
#             },
#         }

#     except NotFoundError as e:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=str(e),
#         )

#     except DuplicateError as e:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail=str(e),
#         )

#     except Exception:
#         logger.exception("session_ingest_failed")

#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Internal server error",
#         )

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

        


