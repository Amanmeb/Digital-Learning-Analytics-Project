# Student registration logic -- manual, CSV, and Excel import
# Supports D3 (auto-generated or manual student ID), D8 pattern reuse
import io
import uuid
from datetime import datetime

from sqlalchemy import text

from login_app.auth import hash_password

MAX_FILE_SIZE = 10 * 1024 * 1024


def generate_student_id(db, school_id):
    # Generates student ID in format SCHOOLID-YEAR-SEQUENCE
    # school_id already encodes country and region, e.g. ET-AA-001
    # Example result: ET-AA-001-2026-000001
    year = str(datetime.utcnow().year)

    count_result = db.execute(
        text("""
            SELECT count(*) FROM mart.dim_student
            WHERE school_id = :school_id
            AND student_id LIKE :pattern
        """),
        {"school_id": school_id, "pattern": school_id + "-" + year + "-%"},
    ).scalar()

    sequence = str(count_result + 1).zfill(6)
    return school_id + "-" + year + "-" + sequence


def register_student(
    db,
    school_id,
    full_name,
    grade_id,
    gender,
    language_preference="English",
    id_type="password",
    credential=None,
    class_id=None,
    student_id=None,
):
    # Registers one student -- inserts into both dim_student and
    # ops.student_auth in the same transaction
    # student_id is auto-generated if not provided, per D3
    if student_id is None:
        student_id = generate_student_id(db, school_id)

    country_code = school_id.split("-")[0]

    try:
        db.execute(
            text("""
                INSERT INTO mart.dim_student
                    (student_id, school_id, grade_id, gender,
                     registration_date, is_active)
                VALUES
                    (:student_id, :school_id, :grade_id, :gender,
                     current_date, true)
            """),
            {
                "student_id": student_id,
                "school_id":  school_id,
                "grade_id":   grade_id,
                "gender":     gender,
            },
        )

        password_hash = None
        pin_hash = None
        if credential:
            if id_type == "pin":
                pin_hash = hash_password(credential)
            else:
                password_hash = hash_password(credential)

        db.execute(
            text("""
                INSERT INTO ops.student_auth
                    (student_id, full_name, class_id, id_type,
                     password_hash, pin_hash, language_preference,
                     country_code, enrollment_date)
                VALUES
                    (:student_id, :full_name, :class_id, :id_type,
                     :password_hash, :pin_hash, :language_preference,
                     :country_code, current_date)
            """),
            {
                "student_id":          student_id,
                "full_name":           full_name,
                "class_id":            class_id,
                "id_type":             id_type,
                "password_hash":       password_hash,
                "pin_hash":            pin_hash,
                "language_preference": language_preference,
                "country_code":        country_code,
            },
        )
        db.commit()
        return True, student_id, ""
    except Exception as e:
        db.rollback()
        return False, None, str(e)


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


def import_students_bulk(db, school_id, file_bytes, filename):
    # Imports students from CSV or Excel
    # Required columns: full_name, grade_id, gender
    # Optional columns: language_preference, id_type, credential, class_id
    rows = parse_file(file_bytes, filename)

    received = len(rows)
    inserted = 0
    invalid = 0
    quarantine = []

    for row in rows:
        required = ["full_name", "grade_id", "gender"]
        missing = [f for f in required if f not in row or not row[f]]
        if missing:
            invalid += 1
            quarantine.append({"row": row, "errors": ["Missing: " + str(missing)]})
            continue

        success, student_id, error = register_student(
            db,
            school_id=school_id,
            full_name=str(row["full_name"]),
            grade_id=str(row["grade_id"]),
            gender=str(row["gender"]),
            language_preference=str(row.get("language_preference", "English")),
            id_type=str(row.get("id_type", "password")),
            credential=str(row["credential"]) if row.get("credential") else None,
            class_id=str(row["class_id"]) if row.get("class_id") else None,
        )

        if success:
            inserted += 1
        else:
            invalid += 1
            quarantine.append({"row": row, "errors": [error]})

    return {
        "received":   received,
        "inserted":   inserted,
        "invalid":    invalid,
        "quarantine": quarantine[:20],
    }