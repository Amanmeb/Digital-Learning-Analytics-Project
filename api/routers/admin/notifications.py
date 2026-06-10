# Notification endpoints
# Returns alerts for schools not syncing, low sync health,
# storage issues, dbt failures, and import failures

from fastapi import APIRouter, Depends
from sqlalchemy import text
from api.database import get_db
from api.routers.admin.settings import get_setting

router = APIRouter(tags=["Admin - Notifications"])


@router.get("/notifications")
def get_notifications(db=Depends(get_db)):
    # Returns all active system notifications
    notifications = []

    # Check schools not synced in X days
    backlog_low = int(get_setting(db, "backlog_alert_low", "global") or 3)

    stale_schools = db.execute(
        text("""
            SELECT school_id, school_name, last_sync_date
            FROM mart.dim_school
            WHERE is_active = TRUE
            AND last_sync_date < CURRENT_DATE - INTERVAL :days
        """),
        {"days": str(backlog_low) + " days"}
    ).fetchall()

    for school in stale_schools:
        notifications.append({
            "type":     "stale_school",
            "level":    "warning",
            "message":  school.school_name + " has not synced in over " +
                        str(backlog_low) + " days",
            "school_id": school.school_id,
        })

    # Check sync health below target
    sync_target = float(get_setting(db, "sync_health_target", "global") or 95)

    sync_health = db.execute(
        text("""
            SELECT
                school_id,
                COUNT(*) FILTER (WHERE status = 'ok') * 100.0 / COUNT(*) as health_pct
            FROM ops.sync_log
            WHERE synced_at > NOW() - INTERVAL '7 days'
            GROUP BY school_id
            HAVING COUNT(*) FILTER (WHERE status = 'ok') * 100.0 / COUNT(*) < :target
        """),
        {"target": sync_target}
    ).fetchall()

    for school in sync_health:
        notifications.append({
            "type":      "low_sync_health",
            "level":     "warning",
            "message":   "School " + school.school_id + " sync health is below target",
            "school_id": school.school_id,
        })

    # Check for recent import failures
    import_failures = db.execute(
        text("""
            SELECT school_id, file_name, rows_invalid, imported_at
            FROM ops.manual_import_log
            WHERE rows_invalid > 0
            AND imported_at > NOW() - INTERVAL '24 hours'
            ORDER BY imported_at DESC
            LIMIT 10
        """)
    ).fetchall()

    for imp in import_failures:
        notifications.append({
            "type":    "import_failure",
            "level":   "info",
            "message": "Import " + (imp.file_name or "unknown") +
                       " had " + str(imp.rows_invalid) + " invalid rows",
            "school_id": imp.school_id,
        })

    return {
        "count":         len(notifications),
        "notifications": notifications,
    }
