# Region management endpoints

from fastapi import APIRouter, Depends
from sqlalchemy import text
from api.database import get_db

router = APIRouter(tags=["Admin - Regions"])


@router.get("/regions")
def list_regions(db=Depends(get_db)):
    # Returns all active regions
    results = db.execute(
        text("""
            SELECT region_id, region_name, country, is_active
            FROM mart.dim_region
            WHERE is_active = TRUE
            ORDER BY region_name
        """)
    ).fetchall()
    return [dict(r._mapping) for r in results]


@router.post("/regions")
def create_region(region: dict, db=Depends(get_db)):
    # Creates a new region
    required = ["region_id", "region_name"]
    for field in required:
        if field not in region:
            return {"error": "Missing required field: " + field}

    existing = db.execute(
        text("SELECT region_id FROM mart.dim_region WHERE region_id = :rid"),
        {"rid": region["region_id"]}
    ).fetchone()

    if existing:
        return {"status": "exists", "region_id": region["region_id"]}

    db.execute(
        text("""
            INSERT INTO mart.dim_region (region_id, region_name, country, is_active)
            VALUES (:region_id, :region_name, :country, TRUE)
        """),
        {
            "region_id":   region["region_id"],
            "region_name": region["region_name"],
            "country":     region.get("country", "Ethiopia"),
        }
    )
    db.commit()
    return {"status": "created", "region_id": region["region_id"]}
