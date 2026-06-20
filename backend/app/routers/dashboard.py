from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

from app.auth.deps import get_current_user

from app.services.dashboard import get_dashboard_summary
from app.auth.rbac import require_roles
from app.schemas.dashboard import DashboardSummaryResponse

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)

# ADMIN + TEACHER REPORTS ONLY

@router.get("/reports")
async def reports(
    user=Depends(require_roles("admin", "teacher"))
):
    return {
        "message": "Teacher or admin access granted",
        "user": user
    }

@router.get("/summary",response_model=DashboardSummaryResponse)
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await get_dashboard_summary(db, user) 
    # return await get_dashboard_summary(db, user["role"])



