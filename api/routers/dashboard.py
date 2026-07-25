from fastapi import APIRouter, Depends
from sqlalchemy import text

from api.database import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _all_rows(result):
    return [dict(row) for row in result.mappings().all()]


@router.get("/summary")
def dashboard_summary(db=Depends(get_db)):
    result = db.execute(
        text("""
            SELECT
                (SELECT COUNT(*) FROM mart.dim_student) AS students,
                (SELECT COUNT(*) FROM mart.dim_teacher) AS teachers,
                (SELECT COUNT(*) FROM mart.dim_school) AS schools,
                (SELECT COUNT(*) FROM mart.fact_session) AS sessions,
                (SELECT COUNT(*) FROM mart.dim_device WHERE is_active = true) AS devices
        """)
    )

    cards = dict(result.mappings().first() or {})
    return {
        "scope": "admin",
        "cards": cards,
        "charts": [],
        "recent_activity": [],
    }


@router.get("/school")
def school_dashboard(db=Depends(get_db)):
    result = db.execute(
        text("""
            SELECT
                school_id,
                school_name,
                region_geo_id,
                school_type,
                total_students,
                active_students,
                total_sessions,
                total_learning_hours,
                registration_coverage_pct,
                performance_index,
                last_active_date,
                risk_flag,
                refreshed_at
            FROM mart.mart_school_performance
            ORDER BY performance_index DESC NULLS LAST
        """)
    )

    return {"data": _all_rows(result)}


@router.get("/platform")
def platform_dashboard(db=Depends(get_db)):
    result = db.execute(
    text("""
        SELECT
            school_id,
            platform_id,
            platform_name,
            platform_type,
            tracking_depth,
            unique_students,
            total_sessions,
            avg_session_minutes,
            total_minutes,
            offline_sessions,
            offline_pct,
            completion_rate_pct,
            total_ai_queries,
            students_used_ai,
            sync_health_pct,
            total_syncs,
            successful_syncs,
            active_devices,
            avg_usage_minutes,
            total_usage_minutes,
            refreshed_at
        FROM mart.mart_platform_analytics
        ORDER BY total_sessions DESC
    """)
)

    return {"data": _all_rows(result)}


@router.get("/device")
def device_dashboard(db=Depends(get_db)):
    result = db.execute(
        text("""
            SELECT
                device_id,
                school_id,
                device_name,
                device_type,
                os,
                assigned_location,
                health_score,
                bandwidth_used_mb_daily,
                last_seen_at,
                health_status,
                refreshed_at
            FROM mart.mart_device_health
            ORDER BY health_score ASC NULLS LAST
        """)
    )

    return {"data": _all_rows(result)}


@router.get("/reports")
def dashboard_reports():
    return {
        "message": "Dashboard reports endpoint is available",
        "reports": [
            "summary",
            "school",
            "platform",
            "device",
        ],
    }
