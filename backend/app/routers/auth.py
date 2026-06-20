from fastapi import APIRouter, Depends

from app.auth.deps import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


