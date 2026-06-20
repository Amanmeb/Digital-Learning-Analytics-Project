from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# from sqlalchemy.exc import IntegrityError


# async def ingest_session(payload: dict, db):
#     try:
#         session = FactSession(
#             session_id=payload["session_id"],
#             student_id=payload["student_id"],
#             school_id=payload["school_id"],
#             device_id=payload["device_id"],
#             platform_id=payload["platform_id"],
#             date_key=payload["date_id"],
#             project_id=payload["project_id"],
#             session_duration_minutes=payload["session_duration_minutes"],
#             is_offline=payload["is_offline"],
#         )

#         db.add(session)
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
    

    
#  from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# from app.config import settings

# engine = create_async_engine(settings.async_database_url, echo=False, pool_pre_ping=True)
# AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# async def get_db():
#     async with AsyncSessionLocal() as session:
#         yield session
