# CDLAID Login App -- student-facing entry point, replaces Moodle
import os
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from login_app.database import get_db, check_db_connection
from login_app.auth import authenticate_student, get_setting
from login_app.registration import register_student, import_students_bulk
from fastapi import Header, File, UploadFile

SCHOOL_ID = os.environ.get("SCHOOL_ID", "ET-AA-001")
SERVER_ID = os.environ.get("SERVER_ID", "SRV-ET-AA-001-001")
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "")


def validate_admin_key(x_admin_key=Header(None)):
    # Validates the admin API key from request header
    # Full admin login UI is a separate future task
    return x_admin_key == ADMIN_API_KEY and ADMIN_API_KEY != ""

app = FastAPI(title="CDLAID Login App")
templates = Jinja2Templates(directory="login_app/templates")
app.mount("/assets", StaticFiles(directory="login_app/assets"), name="assets")


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    # Shows the login form with Camara and school branding
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
    )


@app.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    student_id: str = Form(...),
    credential: str = Form(...),
    db=Depends(get_db),
):
    # Authenticates the student and starts a tracking session
    success, error_message, student = authenticate_student(db, student_id, credential)
    if not success:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": error_message},
        )

    session_id = str(uuid.uuid4())
    login_time = datetime.now(timezone.utc).isoformat()

    # Creates the fact_session row at login time
    # device_id, platform_id, date_key left null -- not captured at this stage
    db.execute(
        text("""
            INSERT INTO mart.fact_session
            (session_id, student_id, school_id, session_start, is_offline, session_duration_minutes)
            VALUES (:session_id, :student_id, :school_id, :session_start, TRUE, 0)
        """),
        {
            "session_id": session_id,
            "student_id": student_id,
            "school_id": SCHOOL_ID,
            "session_start": login_time,
        },
    )
    db.commit()

    response = RedirectResponse(url="/welcome", status_code=303)
    response.set_cookie("student_id", student_id, httponly=True)
    response.set_cookie("session_id", session_id, httponly=True)
    response.set_cookie("login_time", login_time, httponly=True)
    response.set_cookie("full_name", student["full_name"], httponly=True)
    return response


@app.get("/welcome", response_class=HTMLResponse)
async def welcome(request: Request, db=Depends(get_db)):
    # Shows the post-login welcome screen with a simple time counter
    student_id = request.cookies.get("student_id")
    session_id = request.cookies.get("session_id")
    full_name = request.cookies.get("full_name")
    if not student_id:
        return RedirectResponse(url="/login")

    today_minutes = db.execute(
        text("""
            SELECT coalesce(sum(session_duration_minutes), 0)
            FROM mart.fact_session
            WHERE student_id = :student_id
            AND session_start::date = current_date
        """),
        {"student_id": student_id},
    ).scalar()

    daily_goal = int(get_setting(db, "daily_learning_goal_minutes", "60"))

    return templates.TemplateResponse(
        "welcome.html",
        {
            "request": request,
            "full_name": full_name,
            "today_minutes": today_minutes,
            "daily_goal": daily_goal,
            "student_id": student_id,
            "session_id": session_id,
        },
    )


@app.post("/logout")
async def logout(request: Request, db=Depends(get_db)):
    # Closes the fact_session row and clears cookies
    session_id = request.cookies.get("session_id")
    login_time = request.cookies.get("login_time")

    if session_id and login_time:
        logout_dt = datetime.now(timezone.utc)
        login_dt = datetime.fromisoformat(login_time)
        duration_minutes = int((logout_dt - login_dt).total_seconds() / 60)

        db.execute(
            text("""
                UPDATE mart.fact_session
                SET session_end = :session_end, session_duration_minutes = :duration
                WHERE session_id = :session_id
            """),
            {
                "session_end": logout_dt.isoformat(),
                "duration": duration_minutes,
                "session_id": session_id,
            },
        )
        db.commit()

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("student_id")
    response.delete_cookie("session_id")
    response.delete_cookie("login_time")
    response.delete_cookie("full_name")
    return response


@app.post("/admin/students/register")
async def admin_register_student(
    full_name: str = Form(...),
    grade_id: str = Form(...),
    gender: str = Form(...),
    language_preference: str = Form("English"),
    id_type: str = Form("password"),
    credential: str = Form(None),
    class_id: str = Form(None),
    x_admin_key: str = Header(None),
    db=Depends(get_db),
):
    # Registers a single student manually
    if not validate_admin_key(x_admin_key):
        return {"error": "Invalid or missing admin key"}

    success, student_id, error = register_student(
        db,
        school_id=SCHOOL_ID,
        full_name=full_name,
        grade_id=grade_id,
        gender=gender,
        language_preference=language_preference,
        id_type=id_type,
        credential=credential,
        class_id=class_id,
    )
    if not success:
        return {"success": False, "error": error}
    return {"success": True, "student_id": student_id}


@app.post("/admin/students/import")
async def admin_import_students(
    file: UploadFile = File(...),
    x_admin_key: str = Header(None),
    db=Depends(get_db),
):
    # Imports students in bulk from CSV or Excel
    if not validate_admin_key(x_admin_key):
        return {"error": "Invalid or missing admin key"}

    file_bytes = await file.read()
    try:
        result = import_students_bulk(db, SCHOOL_ID, file_bytes, file.filename)
    except ValueError as e:
        return {"error": str(e)}
    return result


@app.get("/health")
async def health():
    # Simple health check endpoint
    db_ok = check_db_connection()
    return {"status": "ok" if db_ok else "db_unreachable"}