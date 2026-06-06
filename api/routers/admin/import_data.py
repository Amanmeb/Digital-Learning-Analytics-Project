# Manual data import endpoints
# Supports CSV and Excel file uploads
# All imports use SHA-256 deduplication

import io
import uuid
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, UploadFile, Request
from sqlalchemy import text

from api.database import get_db
from api.fingerprint import calculate_fingerprint_from_parts
from api.logger import logger

router = APIRouter(tags=["Admin - Import"])

MAX_FILE_SIZE = 10 * 1024 * 1024


def parse_file(file_bytes, filename):
    # Parses CSV or Excel file and returns list of row dicts
    import pandas as pd

    if filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes))
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(file_bytes))
    else:
        raise ValueError("Unsupported file format: " + filename)

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df.to_dict(orient="records")


def write_import_log(db, school_id, filename, file_type, data_type,
                     received, inserted, duplicate, invalid, request_id=None):
    # Writes import result to ops.manual_import_log
    try:
        db.execute(
            text("""
                INSERT INTO ops.manual_import_log
                    (school_id, imported_by, file_name, file_type, data_type,
                     rows_received, rows_inserted, rows_duplicate, rows_invalid,
                     import_source)
                VALUES
                    (:school_id, :imported_by, :file_name, :file_type, :data_type,
                     :received, :inserted, :duplicate, :invalid, :source)
            """),
            {
                "school_id":   school_id,
                "imported_by": "admin_panel",
                "file_name":   filename,
                "file_type":   file_type,
                "data_type":   data_type,
                "received":    received,
                "inserted":    inserted,
                "duplicate":   duplicate,
                "invalid":     invalid,
                "source":      "manual_csv",
            }
        )
        db.commit()
    except Exception as e:
        logger.warning("Import log write failed: " + str(e))


@router.post("/import/sessions")
async def import_sessions(
    request: Request,
    file: UploadFile = File(...),
    db=Depends(get_db),
):
    # Imports session data from CSV or Excel
    # Required columns: student_id, school_id, platform_id,
    #                   session_start, session_end, is_offline
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        return {"error": "E013", "message": "File too large"}

    try:
        rows = parse_file(file_bytes, file.filename)
    except ValueError as e:
        return {"error": "E012", "message": str(e)}

    received = len(rows)
    inserted = 0
    duplicate = 0
    invalid = 0
    quarantine = []

    for row in rows:
        required = ["student_id", "school_id", "session_start"]
        missing = [f for f in required if f not in row or not row[f]]
        if missing:
            invalid += 1
            quarantine.append({"row": row, "errors": ["Missing: " + str(missing)]})
            continue

        fingerprint = calculate_fingerprint_from_parts(
            student_id=str(row.get("student_id", "")),
            event_type="session_import",
            content_id=str(row.get("platform_id", "")),
            timestamp=str(row.get("session_start", "")),
            school_id=str(row.get("school_id", "")),
        )

        existing = db.execute(
            text("SELECT 1 FROM mart.fact_session WHERE event_fingerprint = :fp"),
            {"fp": fingerprint}
        ).fetchone()

        if existing:
            duplicate += 1
            continue

        try:
            session_id = "IMP-SES-" + str(uuid.uuid4())
            db.execute(
                text("""
                    INSERT INTO mart.fact_session
                        (session_id, student_id, school_id, platform_id,
                         is_offline, session_start, event_fingerprint, created_at)
                    VALUES
                        (:session_id, :student_id, :school_id, :platform_id,
                         :is_offline, :session_start, :fingerprint, NOW())
                """),
                {
                    "session_id":    session_id,
                    "student_id":    str(row.get("student_id", "")),
                    "school_id":     str(row.get("school_id", "")),
                    "platform_id":   str(row.get("platform_id", "PLT_OA")),
                    "is_offline":    bool(row.get("is_offline", True)),
                    "session_start": row.get("session_start"),
                    "fingerprint":   fingerprint,
                }
            )
            db.commit()
            inserted += 1
        except Exception as e:
            db.rollback()
            invalid += 1
            quarantine.append({"row": row, "errors": [str(e)]})

    school_id = rows[0].get("school_id", "unknown") if rows else "unknown"
    file_type = "xlsx" if file.filename.endswith((".xlsx", ".xls")) else "csv"
    write_import_log(db, school_id, file.filename, file_type, "sessions",
                     received, inserted, duplicate, invalid)

    return {
        "file":      file.filename,
        "received":  received,
        "inserted":  inserted,
        "duplicate": duplicate,
        "invalid":   invalid,
        "quarantine": quarantine[:20],
    }


@router.post("/import/assessments")
async def import_assessments(
    request: Request,
    file: UploadFile = File(...),
    db=Depends(get_db),
):
    # Imports assessment attempt data from CSV or Excel
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        return {"error": "E013", "message": "File too large"}

    try:
        rows = parse_file(file_bytes, file.filename)
    except ValueError as e:
        return {"error": "E012", "message": str(e)}

    received = len(rows)
    inserted = 0
    duplicate = 0
    invalid = 0
    quarantine = []

    for row in rows:
        required = ["student_id", "school_id", "content_id", "score"]
        missing = [f for f in required if f not in row or row[f] == ""]
        if missing:
            invalid += 1
            quarantine.append({"row": row, "errors": ["Missing: " + str(missing)]})
            continue

        try:
            score = float(row["score"])
            if score < 0 or score > 100:
                raise ValueError("Score out of range")
        except (ValueError, TypeError) as e:
            invalid += 1
            quarantine.append({"row": row, "errors": ["E007: " + str(e)]})
            continue

        fingerprint = calculate_fingerprint_from_parts(
            student_id=str(row.get("student_id", "")),
            event_type="assessment_import",
            content_id=str(row.get("content_id", "")),
            timestamp=str(row.get("attempt_date", "")),
            school_id=str(row.get("school_id", "")),
        )

        existing = db.execute(
            text("SELECT 1 FROM mart.fact_assessment_attempt WHERE event_fingerprint = :fp"),
            {"fp": fingerprint}
        ).fetchone()

        if existing:
            duplicate += 1
            continue

        try:
            attempt_id = "IMP-ATT-" + str(uuid.uuid4())
            db.execute(
                text("""
                    INSERT INTO mart.fact_assessment_attempt
                        (attempt_id, student_id, content_id, score,
                         attempt_number, event_fingerprint, created_at)
                    VALUES
                        (:attempt_id, :student_id, :content_id, :score,
                         :attempt_number, :fingerprint, NOW())
                """),
                {
                    "attempt_id":     attempt_id,
                    "student_id":     str(row.get("student_id", "")),
                    "content_id":     str(row.get("content_id", "")),
                    "score":          score,
                    "attempt_number": int(row.get("attempt_number", 1)),
                    "fingerprint":    fingerprint,
                }
            )
            db.commit()
            inserted += 1
        except Exception as e:
            db.rollback()
            invalid += 1
            quarantine.append({"row": row, "errors": [str(e)]})

    school_id = rows[0].get("school_id", "unknown") if rows else "unknown"
    file_type = "xlsx" if file.filename.endswith((".xlsx", ".xls")) else "csv"
    write_import_log(db, school_id, file.filename, file_type, "assessments",
                     received, inserted, duplicate, invalid)

    return {
        "file":       file.filename,
        "received":   received,
        "inserted":   inserted,
        "duplicate":  duplicate,
        "invalid":    invalid,
        "quarantine": quarantine[:20],
    }
