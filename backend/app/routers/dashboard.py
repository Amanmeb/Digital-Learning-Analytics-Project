from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.auth.rbac import require_roles
from app.auth.roles import Roles
from app.database import get_db
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard import get_dashboard_summary

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



