# Import template download endpoints
# Serves downloadable CSV templates for manual data import

from fastapi import APIRouter
from fastapi.responses import FileResponse
import os

router = APIRouter(tags=["Admin - Templates"])

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "templates")


@router.get("/templates/{template_type}")
def download_template(template_type):
    # Returns a downloadable import template file
    valid_types = ["sessions", "assessments", "content_usage", "ai_usage"]
    if template_type not in valid_types:
        return {"error": "Invalid template type. Valid types: " + str(valid_types)}

    filename = template_type + "_template.csv"
    filepath = os.path.join(TEMPLATES_DIR, filename)

    if not os.path.exists(filepath):
        return {"error": "Template file not found: " + filename}

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="text/csv",
    )
