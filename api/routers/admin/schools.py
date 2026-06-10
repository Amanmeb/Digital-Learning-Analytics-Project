# School registration and management endpoints

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text

from api.database import get_db
from api.logger import log_to_audit

router = APIRouter(tags=["Admin - Schools"])


@router.post("/schools")
def register_school(request: Request, school: dict, db=Depends(get_db)):
    # Registers a new school in dim_school
    # Required fields: school_id, school_name, region_id
    required = ["school_id", "school_name", "region_id"]
    for field in required:
        if field not in school:
            return {"error": "Missing required field: " + field}

    now = datetime.now(timezone.utc)

    # Check if school already exists
    existing = db.execute(
        text("SELECT school_id FROM mart.dim_school WHERE school_id = :sid"),
        {"sid": school["school_id"]}
    ).fetchone()

    if existing:
        return {"status": "exists", "school_id": school["school_id"]}

    db.execute(
        text("""
            INSERT INTO mart.dim_school
                (school_id, school_name, region_id, school_type,
                 is_active, created_at, updated_at)
            VALUES
                (:school_id, :school_name, :region_id, :school_type,
                 TRUE, :now, :now)
        """),
        {
            "school_id":   school["school_id"],
            "school_name": school["school_name"],
            "region_id":   school["region_id"],
            "school_type": school.get("school_type", "Government"),
            "now":         now,
        }
    )
    db.commit()

    log_to_audit(
        db,
        user_name="api",
        action="REGISTER_SCHOOL",
        school_id=school["school_id"],
        table_name="mart.dim_school",
        record_count=1,
        request_id=getattr(request.state, "request_id", None),
    )

    return {"status": "created", "school_id": school["school_id"]}


@router.put("/schools/{school_id}")
def update_school(school_id, request: Request, updates: dict, db=Depends(get_db)):
    # Updates an existing school record
    now = datetime.now(timezone.utc)
    db.execute(
        text("""
            UPDATE mart.dim_school
            SET
                school_name = COALESCE(:school_name, school_name),
                school_type = COALESCE(:school_type, school_type),
                updated_at  = :now
            WHERE school_id = :school_id
        """),
        {
            "school_id":   school_id,
            "school_name": updates.get("school_name"),
            "school_type": updates.get("school_type"),
            "now":         now,
        }
    )
    db.commit()
    return {"status": "updated", "school_id": school_id}


@router.get("/schools")
def list_schools(db=Depends(get_db)):
    # Returns all active schools
    results = db.execute(
        text("""
            SELECT school_id, school_name, region_id, school_type,
                   last_sync_date, is_active
            FROM mart.dim_school
            WHERE is_active = TRUE
            ORDER BY school_name
        """)
    ).fetchall()
    return [dict(r._mapping) for r in results]
