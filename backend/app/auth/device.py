from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.database import get_db
from app.auth.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["device"])

@router.post("/register-device")
async def register_device(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):

    await db.execute(
        text("""
            INSERT INTO mart.user_device (user_id, device_id, is_active)
            VALUES (:user_id, :device_id, true)
            ON CONFLICT (user_id, device_id)
            DO UPDATE SET is_active = true
        """),
        {
            "user_id": user["user_id"],
            "device_id": device_id,
        },
    )

    await db.commit()

    return {
        "status": "device_registered",
        "device_id": device_id,
    }

async def validate_device(
    db: AsyncSession,
    user_id: str,
    device_id: str,
):
    result = await db.execute(
        text("""
            SELECT 1
            FROM core.user_device
            WHERE user_id = :user_id
              AND device_id = :device_id
              AND is_active = TRUE
        """),
        {
            "user_id": user_id,
            "device_id": device_id,
        },
    )

    if not result.scalar():
        raise HTTPException(
            status_code=403,
            detail="Device not registered for user",
        )
    
# async def validate_device(
#     db: AsyncSession,
#     user_id: str,
#     device_id: str,
# ):
#     result = await db.execute(
#         text("""
#             SELECT 1
#             FROM core.user_device
#             WHERE user_id = :user_id
#               AND device_id = :device_id
#               AND is_active = true
#         """),
#         {"user_id": user_id, "device_id": device_id},
#     )

#     if not result.scalar():
#         raise HTTPException(
#             status_code=403,
#             detail="Device not registered for user",
#         )