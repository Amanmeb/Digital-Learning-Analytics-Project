# Authentication logic for the login app
# Handles password and PIN hashing, verification, and lockout tracking
import bcrypt
from sqlalchemy import text


def hash_password(plain_password):
    # Returns a bcrypt hash of the given password or PIN
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password, password_hash):
    # Returns True if plain_password matches the stored hash
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except Exception:
        return False


def get_setting(db, setting_key, default_value):
    # Reads a single setting value from ops.settings
    # Returns default_value if the setting does not exist
    result = db.execute(
        text("SELECT setting_value FROM ops.settings WHERE setting_key = :key"),
        {"key": setting_key},
    ).fetchone()
    if result is None:
        return default_value
    return result[0]


def get_student_auth(db, student_id):
    # Returns the student_auth row as a dict, or None if not found
    result = db.execute(
        text("""
            SELECT student_id, full_name, class_id, id_type, password_hash,
                   pin_hash, failed_login_count, is_locked, graduation_status
            FROM ops.student_auth
            WHERE student_id = :student_id
        """),
        {"student_id": student_id},
    ).fetchone()
    if result is None:
        return None
    return dict(result._mapping)


def record_failed_login(db, student_id):
    # Increments failed_login_count and locks the account if the
    # configured maximum is reached. A max of 0 means no lockout.
    max_attempts = int(get_setting(db, "failed_login_max_attempts", "0"))

    db.execute(
        text("""
            UPDATE ops.student_auth
            SET failed_login_count = failed_login_count + 1,
                updated_at = now()
            WHERE student_id = :student_id
        """),
        {"student_id": student_id},
    )

    if max_attempts > 0:
        db.execute(
            text("""
                UPDATE ops.student_auth
                SET is_locked = true
                WHERE student_id = :student_id
                AND failed_login_count >= :max_attempts
            """),
            {"student_id": student_id, "max_attempts": max_attempts},
        )

    db.commit()


def record_successful_login(db, student_id):
    # Resets failed_login_count on a successful login
    db.execute(
        text("""
            UPDATE ops.student_auth
            SET failed_login_count = 0,
                updated_at = now()
            WHERE student_id = :student_id
        """),
        {"student_id": student_id},
    )
    db.commit()


def authenticate_student(db, student_id, credential):
    # Returns (success, error_message, student_auth_dict)
    # Checks lockout, graduation status, and verifies password or PIN
    student = get_student_auth(db, student_id)
    if student is None:
        return False, "Student ID not found", None

    if student["is_locked"]:
        return False, "Account is locked, contact your admin", None

    if student["graduation_status"] != "active":
        return False, "Account is not active", None

    if student["id_type"] == "pin":
        credential_valid = verify_password(credential, student["pin_hash"])
    else:
        credential_valid = verify_password(credential, student["password_hash"])

    if not credential_valid:
        record_failed_login(db, student_id)
        return False, "Incorrect password or PIN", None

    record_successful_login(db, student_id)
    return True, "", student