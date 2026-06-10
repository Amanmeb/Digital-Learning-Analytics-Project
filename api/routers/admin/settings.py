# Settings management endpoints
# Reads and writes to ops.settings table
# Falls back to code defaults if setting not found
from fastapi import APIRouter, Depends
from sqlalchemy import text
from datetime import datetime, timezone
from api.database import get_db
router = APIRouter(tags=["Admin - Settings"])
DEFAULTS = {
    "top_n_default":                "10",
    "pass_threshold":               "50",
    "mastery_threshold":            "80",
    "ai_adoption_target":           "30",
    "gender_parity_min":            "0.9",
    "gender_parity_max":            "1.1",
    "completion_flag":              "40",
    "school_coverage_flag":         "50",
    "school_performance_flag":      "0.4",
    "inactivity_cutoff_min":        "30",
    "reengagement_days":            "14",
    "sync_health_target":           "95",
    "content_stale_days":           "365",
    "first_week_days":              "7",
    "date_range_default":           "30",
    "chart_granularity":            "Monthly",
    "demo_mode":                    "false",
    "dashboard_language":           "English",
    "auto_refresh":                 "false",
    "primary_color":                "#81BC00",
    "secondary_color":              "#375C7A",
    "accent_color":                 "#943266",
    "learning_engagement_weights":  "{\"activity_participation\":0.30,\"session_duration\":0.30,\"content_completion\":0.20,\"ai_usage\":0.20}",
    "school_performance_weights":   "{\"active_rate\":0.25,\"avg_score\":0.25,\"completion_rate\":0.25,\"ai_adoption\":0.25}",
    "student_achievement_weights":  "{\"avg_score\":0.40,\"pass_rate\":0.30,\"score_improvement\":0.30}",
    "ai_impact_weights":            "{\"frequency\":0.25,\"duration\":0.25,\"subject_coverage\":0.25,\"score_improvement\":0.25}",
    "retention_weights":            "{\"returning_users\":0.40,\"active_days\":0.40,\"reengagement\":0.20}",
}
def get_setting(db, key, scope="global"):
    # Returns a setting value from ops.settings
    # Falls back to code default if not found
    result = db.execute(
        text("""
            SELECT setting_value FROM ops.settings
            WHERE setting_key = :key AND setting_scope = :scope
        """),
        {"key": key, "scope": scope}
    ).fetchone()
    if result:
        return result.setting_value
    return DEFAULTS.get(key, "")
@router.get("/settings")
def list_settings(db=Depends(get_db)):
    # Returns all settings with their current values
    results = db.execute(
        text("""
            SELECT setting_key, setting_value, setting_scope, description
            FROM ops.settings
            ORDER BY setting_key
        """)
    ).fetchall()
    return [dict(r._mapping) for r in results]
@router.put("/settings")
def update_setting(update: dict, db=Depends(get_db)):
    # Updates a setting value
    # Required fields: setting_key, setting_value
    required = ["setting_key", "setting_value"]
    for field in required:
        if field not in update:
            return {"error": "Missing required field: " + field}
    now = datetime.now(timezone.utc)
    scope = update.get("setting_scope", "global")
    db.execute(
        text("""
            INSERT INTO ops.settings (setting_key, setting_value, setting_scope, updated_at)
            VALUES (:key, :value, :scope, :now)
            ON CONFLICT (setting_key, setting_scope)
            DO UPDATE SET setting_value = :value, updated_at = :now
        """),
        {
            "key":   update["setting_key"],
            "value": update["setting_value"],
            "scope": scope,
            "now":   now,
        }
    )
    db.commit()
    return {
        "status":        "updated",
        "setting_key":   update["setting_key"],
        "setting_value": update["setting_value"],
    }