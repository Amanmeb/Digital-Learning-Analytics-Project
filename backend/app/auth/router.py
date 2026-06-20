from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.auth.schemas import LoginRequest, RegisterRequest, LogoutRequest, RefreshRequest, LogoutDeviceRequest
from app.auth.security import create_access_token, hash_password, verify_password, create_refresh_token,hash_token, decode_token
from app.database import get_db
from datetime import datetime, timedelta
import secrets
import hashlib
from app.auth.rbac import require_roles
from app.services.audit import log_event

def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.get("/me")
async def me(current_user=Depends(get_current_user)):
    return current_user


@router.post("/login")
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # ---------------------------------------
    # Load user
    # ---------------------------------------
    result = await db.execute(
        text("""
            SELECT
                user_id,
                email,
                password_hash,
                role,
                student_id,
                teacher_id,
                failed_login_attempts,
                locked_until
            FROM auth.users
            WHERE email = :email
              AND is_active = true
        """),
        {"email": payload.email},
    )

    user = result.mappings().first()

    # ---------------------------------------
    # INVALID USER (audit safe)
    # ---------------------------------------
    if not user:
        await log_event(
            db=db,
            # user_id=None,
            user_id=user["user_id"],
            event="login_success",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            device_id=device_id,
            metadata={"role": user["role"]},
        )

        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ---------------------------------------
    # LOCK CHECK
    # ---------------------------------------
    if user["locked_until"] and user["locked_until"] > datetime.utcnow():
        raise HTTPException(status_code=423, detail="Account locked")

    # ---------------------------------------
    # PASSWORD CHECK
    # ---------------------------------------
    if not verify_password(payload.password, user["password_hash"]):

        attempts = user["failed_login_attempts"] + 1
        lock_until = datetime.utcnow() + timedelta(minutes=15) if attempts >= 5 else None

        await db.execute(
            text("""
                UPDATE auth.users
                SET failed_login_attempts = :attempts,
                    last_failed_login = NOW(),
                    locked_until = :lock_until
                WHERE user_id = :user_id
            """),
            {
                "attempts": attempts,
                "lock_until": lock_until,
                "user_id": user["user_id"],
            },
        )

        await log_event(
            db=db,
            user_id=user["user_id"],
            event="login_success",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            device_id=device_id,
            metadata={"role": user["role"]},
        )

        await db.commit()

        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ---------------------------------------
    # SUCCESS LOGIN (USER STATE UPDATE)
    # ---------------------------------------
    await db.execute(
        text("""
            UPDATE auth.users
            SET failed_login_attempts = 0,
                locked_until = NULL,
                last_failed_login = NULL,
                last_login = NOW()
            WHERE user_id = :user_id
        """),
        {"user_id": user["user_id"]},
    )

    # ---------------------------------------
    # TOKENS
    # ---------------------------------------
    token_subject = user["student_id"] or user["teacher_id"] or user["user_id"]

    access_token = create_access_token({
        "sub": str(token_subject),
        "user_id": str(user["user_id"]),
        "role": user["role"],
    })

    refresh_token = create_refresh_token()
    refresh_hash = hash_token(refresh_token)

    # ---------------------------------------
    # DEVICE METADATA
    # ---------------------------------------
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    device_id = request.headers.get("x-device-id") or str(uuid4())
    device_name = request.headers.get("x-device-name")

    # ---------------------------------------
    # STORE REFRESH TOKEN (FIXED)
    # ---------------------------------------
    await db.execute(
        text("""
            INSERT INTO auth.refresh_tokens (
                id,
                user_id,
                token_hash,
                expires_at,
                device_id,
                device_name,
                user_agent,
                ip_address
            )
            VALUES (
                :id,
                :user_id,
                :token_hash,
                :expires_at,
                :device_id,
                :device_name,
                :user_agent,
                :ip_address
            )
        """),
        {
            "id": str(uuid4()),
            "user_id": user["user_id"],
            "token_hash": refresh_hash,
            "expires_at": datetime.utcnow() + timedelta(days=7),
            "device_id": device_id,
            "device_name": device_name,
            "user_agent": user_agent,
            "ip_address": ip_address,
        },
    )

    # ---------------------------------------
    # AUDIT LOG (SUCCESS - AFTER EVERYTHING WORKS)
    # ---------------------------------------
    await log_event(
        db=db,
        user_id=user["user_id"],
        event="login_success",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        device_id=device_id,
        metadata={"role": user["role"]},
    )

    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.get("/sessions")
async def get_sessions(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]

    result = await db.execute(
        text("""
            SELECT
                id,
                device_id,
                device_name,
                user_agent,
                ip_address,
                created_at,
                last_used_at,
                expires_at,
                revoked,
                revoked_at
            FROM auth.refresh_tokens
            WHERE user_id = :user_id
            ORDER BY created_at DESC
        """),
        {"user_id": user_id},
    )

    sessions = result.mappings().all()

    return {
        "active_sessions": [
            {
                **s,
                "is_active": not s["revoked"] and s["expires_at"] > datetime.utcnow()
            }
            for s in sessions
        ]
    }

@router.post("/logout")
async def logout(
    payload: LogoutRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):

    token_hash = hash_token(payload.refresh_token)

    result = await db.execute(
        text("""
            SELECT id
            FROM auth.refresh_tokens
            WHERE token_hash = :token_hash
              AND revoked = false
        """),
        {
            "token_hash": token_hash,
        },
    )

    token = result.mappings().first()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token",
        )

    await db.execute(
        text("""
            UPDATE auth.refresh_tokens
            SET
                revoked = true,
                revoked_at = NOW()
            WHERE id = :id
        """),
        {
            "id": token["id"],
        },
    )
    await log_event(
    db=db,
    user_id=token["user_id"],
    event="logout",
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
)
    await db.commit()

    return {
        "message": "Logged out successfully"
    }

@router.post("/logout-all")
async def logout_all(request: Request,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]

    await db.execute(
        text("""
            UPDATE auth.refresh_tokens
            SET revoked = true,
                revoked_at = NOW()
            WHERE user_id = :user_id
              AND revoked = false
        """),
        {"user_id": user_id},
    )

    await log_event(
    db=db,
    user_id=user_id,
    event="logout_all",
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
)

    await db.commit()

    return {"message": "Logged out from all devices successfully"}

@router.post("/logout-device")
async def logout_device(
    payload: LogoutDeviceRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user["user_id"]

    # ensure session belongs to user
    result = await db.execute(
        text("""
            SELECT id
            FROM auth.refresh_tokens
            WHERE id = :id
              AND user_id = :user_id
              AND revoked = false
        """),
        {
            "id": payload.session_id,
            "user_id": user_id,
        },
    )

    session = result.mappings().first()

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    # revoke only this session
    await db.execute(
        text("""
            UPDATE auth.refresh_tokens
            SET revoked = true,
                revoked_at = NOW()
            WHERE id = :id
        """),
        {"id": payload.session_id},
    )

    await db.commit()

    return {"message": "Device logged out successfully"}

@router.post("/refresh")
async def refresh_token(
    payload: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # ----------------------------------------
    # 1. Hash incoming refresh token
    # ----------------------------------------
    token_hash = hash_token(payload.refresh_token)

    # ----------------------------------------
    # 2. Find token in DB
    # ----------------------------------------
    result = await db.execute(
        text("""
            SELECT id, user_id, expires_at, revoked
            FROM auth.refresh_tokens
            WHERE token_hash = :token_hash
        """),
        {"token_hash": token_hash},
    )

    stored_token = result.mappings().first()

    # ----------------------------------------
    # 3. Validate token existence
    # ----------------------------------------
    if not stored_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # ----------------------------------------
    # 4. Check revoked
    # ----------------------------------------
    if stored_token["revoked"]:
        raise HTTPException(status_code=401, detail="Refresh token revoked")

    # ----------------------------------------
    # 5. Check expiry
    # ----------------------------------------
    if stored_token["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    user_id = stored_token["user_id"]

    # ----------------------------------------
    # 6. Load user (security check)
    # ----------------------------------------
    user_result = await db.execute(
        text("""
            SELECT user_id, role, student_id, teacher_id
            FROM auth.users
            WHERE user_id = :user_id AND is_active = true
        """),
        {"user_id": user_id},
    )

    user = user_result.mappings().first()

    await log_event(
    db=db,
    user_id=stored_token["user_id"],
    event="refresh_token_used",
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    device_id=stored_token["device_id"],
)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # ----------------------------------------
    # 7. ROTATION: revoke old token
    # ----------------------------------------
    await db.execute(
        text("""
            UPDATE auth.refresh_tokens
            SET revoked = true,
                revoked_at = NOW(),
                last_used_at = NOW()
            WHERE id = :id
        """),
        {"id": stored_token["id"]},
    )

    # ----------------------------------------
    # 8. Create new tokens
    # ----------------------------------------
    subject = user["student_id"] or user["teacher_id"] or user["user_id"]

    new_access_token = create_access_token({
        "sub": str(subject),
        "user_id": str(user["user_id"]),
        "role": user["role"],
    })

    new_refresh_token = create_refresh_token()
    new_refresh_hash = hash_token(new_refresh_token)

    # ----------------------------------------
    # 9. Capture device metadata
    # ----------------------------------------
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent")

    # ----------------------------------------
    # 10. Store new refresh token
    # ----------------------------------------
    await db.execute(
        text("""
            INSERT INTO auth.refresh_tokens (
                id,
                user_id,
                token_hash,
                expires_at,
                device_id,
                device_name,
                user_agent,
                ip_address,
                created_at
            )
            VALUES (
                :id,
                :user_id,
                :token_hash,
                :expires_at,
                :device_id,
                :device_name,
                :user_agent,
                :ip_address,
                NOW()
            )
        """),
        {
        "id": str(uuid4()),
        "user_id": user["user_id"],
        # "token_hash": hash_token(refresh_token),
        "token_hash": new_refresh_hash,
        "expires_at": datetime.utcnow() + timedelta(days=7),

        # "device_id": payload.device_id,      
        # "device_name": payload.device_name, 

        "device_id": stored_token["device_id"],
        "device_name": stored_token["device_name"],

        "user_agent": user_agent,
        "ip_address": ip_address,
        },
    )

    await db.commit()

    # ----------------------------------------
    # 11. Return rotated tokens
    # ----------------------------------------
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }

@router.post("/register")
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        text("SELECT 1 FROM auth.users WHERE email = :email"),
        {"email": payload.email},
    )

    if existing.scalar():
        raise HTTPException(status_code=409, detail="Email already exists")

    await db.execute(
        text("""
            INSERT INTO auth.users (
                user_id,
                email,
                password_hash,
                role,
                student_id,
                teacher_id
            )
            VALUES (
                :user_id,
                :email,
                :password_hash,
                :role,
                :student_id,
                :teacher_id
            )
        """),
        {
            "user_id": str(uuid4()),
            "email": payload.email,
            "password_hash": hash_password(payload.password),
            "role": payload.role,
            "student_id": payload.student_id,
            "teacher_id": payload.teacher_id,
        },
    )
    await db.commit()

    return {"message": "User registered"}

@router.post("/sync/users")
async def sync_users(db: AsyncSession = Depends(get_db)):

    result = await db.execute(
        text("""
            SELECT id, local_id, email, password_hash, role, student_id, teacher_id
            FROM auth.sync_user_queue
            WHERE status = 'PENDING'
        """)
    )

    users = result.mappings().all()

    for u in users:
        await db.execute(
            text("""
                INSERT INTO auth.users (
                    user_id,
                    email,
                    password_hash,
                    role,
                    student_id,
                    teacher_id,
                    is_active
                )
                VALUES (
                    :user_id,
                    :email,
                    :password_hash,
                    :role,
                    :student_id,
                    :teacher_id,
                    true
                )
            """),
            {
                "user_id": str(uuid4()),
                "email": u["email"],
                "password_hash": u["password_hash"],
                "role": u["role"],
                "student_id": u["student_id"],
                "teacher_id": u["teacher_id"],
            },
        )

    await db.execute(
        text("""
            UPDATE auth.sync_user_queue
            SET status = 'SYNCED'
            WHERE status = 'PENDING'
        """)
    )

    await db.commit()

    return {
        "synced_users": len(users),
        "message": "Sync completed successfully"
    }

@router.get("/admin/users")
async def get_users(
    current_user=Depends(require_roles("admin"))
):
    return {"message": "Admin access granted"}




    
# @router.post("/login")
# async def login(
#     payload: LoginRequest,
#     db: AsyncSession = Depends(get_db),
# ):
#     # -------------------------
#     # FETCH USER
#     # -------------------------
#     result = await db.execute(
#         text("""
#             SELECT user_id, email, password_hash, role, student_id, teacher_id
#             FROM auth.users
#             WHERE email = :email
#               AND is_active = true
#         """),
#         {"email": payload.email},
#     )

#     user = result.mappings().first()

#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     if not verify_password(payload.password, user["password_hash"]):
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     # -------------------------
#     # ACCESS TOKEN
#     # -------------------------
#     token_subject = (
#         user["student_id"]
#         or user["teacher_id"]
#         or user["user_id"]
#     )

#     access_token = create_access_token(
#         {
#             "sub": str(token_subject),
#             "user_id": str(user["user_id"]),
#             "role": user["role"],
#         }
#     )

#     # -------------------------
#     # REFRESH TOKEN
#     # -------------------------
#     refresh_token = create_refresh_token()

#     await db.execute(
#         text("""
#             INSERT INTO auth.refresh_tokens (
#                 id,
#                 user_id,
#                 token_hash,
#                 expires_at
#             )
#             VALUES (
#                 :id,
#                 :user_id,
#                 :token_hash,
#                 :expires_at
#             )
#         """),
#         {
#             "id": str(uuid4()),
#             "user_id": user["user_id"],
#             "token_hash": hash_token(refresh_token),
#             "expires_at": datetime.utcnow() + timedelta(days=7),
#         },
#     )

#     await db.commit()

#     # -------------------------
#     # RESPONSE
#     # -------------------------
#     return {
#         "access_token": access_token,
#         "refresh_token": refresh_token,
#         "token_type": "bearer",
#     }

#  @router.post("/login")
# async def login(
#     payload: LoginRequest,
#     db: AsyncSession = Depends(get_db),
# ):
#     result = await db.execute(
#         text("""
#             SELECT user_id, email, password_hash, role, student_id, teacher_id
#             FROM auth.users
#             WHERE email = :email
#               AND is_active = true
#         """),
#         {"email": payload.email},
#     )

#     user = result.mappings().first()

#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid credentials")

#     if not verify_password(payload.password, user["password_hash"]):
#         raise HTTPException(status_code=401, detail="Invalid credentials")
    

#     token_subject = user["student_id"] or user["teacher_id"] or user["user_id"]
#     token = create_access_token(
#         {
#             "sub": str(token_subject),
#             "user_id": str(user["user_id"]),
#             "role": user["role"],
#         }
#     )

#     return {
#         "access_token": token,
#         "token_type": "bearer",
#     }
# @router.post("/refresh")
# async def refresh(
#     payload: RefreshTokenRequest,
#     db: AsyncSession = Depends(get_db),
# ):

#     token_hash = hash_token(payload.refresh_token)

#     result = await db.execute(
#         text("""
#             SELECT
#                 rt.id,
#                 rt.user_id,
#                 rt.expires_at,
#                 rt.revoked,

#                 u.role,
#                 u.student_id,
#                 u.teacher_id

#             FROM auth.refresh_tokens rt

#             JOIN auth.users u
#               ON rt.user_id = u.user_id

#             WHERE rt.token_hash = :token_hash
#         """),
#         {
#             "token_hash": token_hash
#         },
#     )

#     session = result.mappings().first()

#     if not session:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid refresh token",
#         )

#     if session["revoked"]:
#         raise HTTPException(
#             status_code=401,
#             detail="Refresh token revoked",
#         )

#     if session["expires_at"] < datetime.utcnow():
#         raise HTTPException(
#             status_code=401,
#             detail="Refresh token expired",
#         )

#     token_subject = (
#         session["student_id"]
#         or session["teacher_id"]
#         or session["user_id"]
#     )

#     access_token = create_access_token(
#         {
#             "sub": str(token_subject),
#             "user_id": str(session["user_id"]),
#             "role": session["role"],
#         }
#     )

#     #
#     # Rotate refresh token
#     #

#     new_refresh_token = create_refresh_token()

#     await db.execute(
#         text("""
#             UPDATE auth.refresh_tokens
#             SET
#                 revoked = true,
#                 revoked_at = NOW()
#             WHERE id = :id
#         """),
#         {
#             "id": session["id"],
#         },
#     )

#     await db.execute(
#         text("""
#             INSERT INTO auth.refresh_tokens
#             (
#                 id,
#                 user_id,
#                 token_hash,
#                 expires_at,
#                 created_at,
#                 device_name,
#                 device_id,
#                 user_agent,
#                 ip_address
#             )
#             VALUES
#             (
#                 :id,
#                 :user_id,
#                 :token_hash,
#                 :expires_at,
#                 NOW(),
#                 NULL,
#                 NULL,
#                 NULL,
#                 NULL
#             )
#         """),
#         {
#             "id": str(uuid4()),
#             "user_id": session["user_id"],
#             "token_hash": hash_token(new_refresh_token),
#             "expires_at": datetime.utcnow() + timedelta(days=7),
#         },
#     )

#     await db.commit()

#     return {
#         "access_token": access_token,
#         "refresh_token": new_refresh_token,
#         "token_type": "bearer",
#     }