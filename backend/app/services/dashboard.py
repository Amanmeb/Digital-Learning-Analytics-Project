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
        "data": dict(row)
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





