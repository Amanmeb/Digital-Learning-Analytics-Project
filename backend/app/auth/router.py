from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.auth.schemas import LoginRequest, RegisterRequest
from app.auth.security import create_access_token, hash_password, verify_password
from app.database import get_db

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
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("""
            SELECT user_id, email, password_hash, role, student_id, teacher_id
            FROM auth.users
            WHERE email = :email
              AND is_active = true
        """),
        {"email": payload.email},
    )

    user = result.mappings().first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_subject = user["student_id"] or user["teacher_id"] or user["user_id"]
    token = create_access_token(
        {
            "sub": str(token_subject),
            "user_id": str(user["user_id"]),
            "role": user["role"],
        }
    )

    return {
        "access_token": token,
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
