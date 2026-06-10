# Project management endpoints

from fastapi import APIRouter, Depends
from sqlalchemy import text
from api.database import get_db

router = APIRouter(tags=["Admin - Projects"])


@router.get("/projects")
def list_projects(db=Depends(get_db)):
    # Returns all active projects
    results = db.execute(
        text("""
            SELECT project_id, project_name, funder,
                   start_date, end_date, is_active
            FROM mart.dim_project
            WHERE is_active = TRUE
            ORDER BY project_name
        """)
    ).fetchall()
    return [dict(r._mapping) for r in results]


@router.post("/projects")
def create_project(project: dict, db=Depends(get_db)):
    # Creates a new project
    required = ["project_id", "project_name"]
    for field in required:
        if field not in project:
            return {"error": "Missing required field: " + field}

    existing = db.execute(
        text("SELECT project_id FROM mart.dim_project WHERE project_id = :pid"),
        {"pid": project["project_id"]}
    ).fetchone()

    if existing:
        return {"status": "exists", "project_id": project["project_id"]}

    db.execute(
        text("""
            INSERT INTO mart.dim_project
                (project_id, project_name, funder, start_date, end_date, is_active)
            VALUES
                (:project_id, :project_name, :funder, :start_date, :end_date, TRUE)
        """),
        {
            "project_id":   project["project_id"],
            "project_name": project["project_name"],
            "funder":       project.get("funder"),
            "start_date":   project.get("start_date"),
            "end_date":     project.get("end_date"),
        }
    )
    db.commit()
    return {"status": "created", "project_id": project["project_id"]}
