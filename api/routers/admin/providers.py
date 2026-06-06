# Content provider management endpoints

from fastapi import APIRouter, Depends
from sqlalchemy import text
from api.database import get_db

router = APIRouter(tags=["Admin - Providers"])


@router.get("/providers")
def list_providers(db=Depends(get_db)):
    # Returns all active content providers
    results = db.execute(
        text("""
            SELECT provider_id, provider_name, provider_type,
                   provider_level, is_active
            FROM mart.dim_content_provider
            WHERE is_active = TRUE
            ORDER BY provider_name
        """)
    ).fetchall()
    return [dict(r._mapping) for r in results]


@router.post("/providers")
def create_provider(provider: dict, db=Depends(get_db)):
    # Creates a new content provider
    required = ["provider_id", "provider_name"]
    for field in required:
        if field not in provider:
            return {"error": "Missing required field: " + field}

    existing = db.execute(
        text("SELECT provider_id FROM mart.dim_content_provider WHERE provider_id = :pid"),
        {"pid": provider["provider_id"]}
    ).fetchone()

    if existing:
        return {"status": "exists", "provider_id": provider["provider_id"]}

    db.execute(
        text("""
            INSERT INTO mart.dim_content_provider
                (provider_id, provider_name, provider_type, provider_level, is_active)
            VALUES
                (:provider_id, :provider_name, :provider_type, :provider_level, TRUE)
        """),
        {
            "provider_id":    provider["provider_id"],
            "provider_name":  provider["provider_name"],
            "provider_type":  provider.get("provider_type", "NGO"),
            "provider_level": provider.get("provider_level", "National"),
        }
    )
    db.commit()
    return {"status": "created", "provider_id": provider["provider_id"]}
