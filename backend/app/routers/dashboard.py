from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.auth.rbac import require_roles
from app.auth.roles import Roles
from app.database import get_db
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard import (
    get_dashboard_summary,
    get_device_dashboard,
    get_platform_dashboard,
    get_school_dashboard,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)

# ADMIN + TEACHER REPORTS ONLY

@router.get("/reports")
async def reports(
    # current_user=Depends(require_roles("admin", "teacher"))
    current_user=Depends(require_roles(Roles.ADMIN, Roles.TEACHER))
    # user=Depends(require_roles(Roles.SCHOOL_ADMIN, Roles.TEACHER))

):
    return {
        "message": "Teacher or admin access granted",
        "user": current_user
        # "user": user
    }

    # return {"ok": True}

@router.get("/summary", response_model=DashboardSummaryResponse)
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await get_dashboard_summary(db, user) 
    # return await get_dashboard_summary(db, user["role"])

@router.get("/school")
async def school_dashboard(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await get_school_dashboard(db, user)

@router.get("/platform")
async def platform_dashboard(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await get_platform_dashboard(db, user)

@router.get("/device")
async def device_dashboard(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await get_device_dashboard(db, user)

