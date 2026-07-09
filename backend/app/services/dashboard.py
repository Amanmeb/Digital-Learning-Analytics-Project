from sqlalchemy import text


async def get_dashboard_summary(db, user):
    role = user.get("role")

    if role == "admin":
        return await admin_dashboard(db)

    if role == "teacher":
        return await teacher_dashboard(db, user)

    return await student_dashboard(db, user)

async def admin_dashboard(db):
    result = await db.execute(
        text("""
            SELECT
                (SELECT COUNT(*) FROM mart.dim_student) AS students,
                (SELECT COUNT(*) FROM mart.dim_teacher) AS teachers,
                (SELECT COUNT(*) FROM mart.dim_school) AS schools,
                (SELECT COUNT(*) FROM mart.fact_session) AS sessions,
                (SELECT COUNT(*) FROM mart.dim_device WHERE is_active = true) AS devices
        """)
    )

    row = result.mappings().first()
    return {
        "scope": "admin",
        "cards": dict(row),
        "charts": [],
        "recent_activity": [],
    }

async def teacher_dashboard(db, user):
    return {
        "scope": "teacher",
        "cards": {
            "students": 0,
            "active_sessions": 0,
            "average_completion": 0,
            "average_score": 0
        },
        "charts": [],
        "recent_activity": []
        # "data": {
        #     "user_id": user["user_id"],
        #     "message": "teacher analytics placeholder"
        # }
    }

async def student_dashboard(db, user):
    return {
        "scope": "student",
        "cards": {
            "sessions": 0,
            "learning_minutes": 0,
            "assignments_completed": 0,
            "average_score": 0
        },
        "charts": [],
        "recent_activity": []
        # "scope": "student",
        # "data": {
        #     "user_id": user["user_id"],
        #     "message": "student analytics placeholder"
        # }
    }

async def get_platform_dashboard(db, user):
    result = await db.execute(
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

    rows = result.mappings().all()

    return {"data": rows}


async def get_school_dashboard(db, user):
    result = await db.execute(
        text("""
            SELECT
                school_id,
                date_key,
                total_syncs,
                successful_syncs,
                sync_health_pct,
                active_devices,
                avg_usage_minutes,
                total_sessions,
                total_usage_minutes,
                refreshed_at
            FROM mart.mart_device_infrastructure
            ORDER BY date_key DESC
        """)
    )

    rows = result.mappings().all()

    return {"data": rows}
                    # school_id,
                # school_name,
                # region_id,
                # school_type,
                # total_students,
                # active_students,
                # total_sessions,
                # total_learning_hours,
                # registration_coverage_pct,
                # performance_index,
                # last_active_date,
                # risk_flag,
                # refreshed_at


async def get_device_dashboard(db, user): 
    result = await db.execute(
        text("""
            SELECT
                school_id,
                date_key,
                total_syncs,
                successful_syncs,
                sync_health_pct,
                active_devices,
                avg_usage_minutes,
                total_sessions,
                total_usage_minutes,
                refreshed_at
            FROM mart.mart_device_infrastructure
            ORDER BY total_usage_minutes DESC
        """)
    )

    rows = result.mappings().all()

    return {"data": rows}






