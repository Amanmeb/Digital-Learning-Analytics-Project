-- Migration 008
-- Application authentication tables
-- CDLAID Analytics Platform

CREATE TABLE IF NOT EXISTS auth.users (
    user_id         UUID PRIMARY KEY,
    email           VARCHAR(320) NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            VARCHAR(50) NOT NULL DEFAULT 'student',
    student_id      VARCHAR(50),
    teacher_id      VARCHAR(50),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auth_users_email
    ON auth.users(email);

CREATE INDEX IF NOT EXISTS idx_auth_users_student
    ON auth.users(student_id)
    WHERE student_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_auth_users_teacher
    ON auth.users(teacher_id)
    WHERE teacher_id IS NOT NULL;

GRANT USAGE ON SCHEMA auth TO cdlaid_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA auth TO cdlaid_user;
