-- Migration 003
-- All 9 fact tables
-- CDLAID Analytics Platform

-- FactSession
CREATE TABLE IF NOT EXISTS mart.fact_session (
    session_id                  VARCHAR(100) PRIMARY KEY,
    student_id                  VARCHAR(50) REFERENCES mart.dim_student(student_id),
    school_id                   VARCHAR(20) REFERENCES mart.dim_school(school_id),
    device_id                   VARCHAR(50) REFERENCES mart.dim_device(device_id),
    platform_id                 VARCHAR(20) REFERENCES mart.dim_platform(platform_id),
    date_key                    INTEGER REFERENCES mart.dim_date(date_key),
    project_id                  VARCHAR(20) REFERENCES mart.dim_project(project_id),
    session_duration_minutes    INTEGER NOT NULL DEFAULT 0,
    is_offline                  BOOLEAN NOT NULL DEFAULT TRUE,
    session_start               TIMESTAMPTZ,
    session_end                 TIMESTAMPTZ,
    event_fingerprint           VARCHAR(64),
    created_at                  TIMESTAMPTZ DEFAULT NOW()
);

-- FactTeacherSession
CREATE TABLE IF NOT EXISTS mart.fact_teacher_session (
    teacher_session_id          VARCHAR(100) PRIMARY KEY,
    teacher_id                  VARCHAR(50) REFERENCES mart.dim_teacher(teacher_id),
    school_id                   VARCHAR(20) REFERENCES mart.dim_school(school_id),
    device_id                   VARCHAR(50) REFERENCES mart.dim_device(device_id),
    platform_id                 VARCHAR(20) REFERENCES mart.dim_platform(platform_id),
    date_key                    INTEGER REFERENCES mart.dim_date(date_key),
    session_duration_minutes    INTEGER NOT NULL DEFAULT 0,
    is_offline                  BOOLEAN NOT NULL DEFAULT TRUE,
    session_start               TIMESTAMPTZ,
    session_end                 TIMESTAMPTZ,
    event_fingerprint           VARCHAR(64),
    created_at                  TIMESTAMPTZ DEFAULT NOW()
);

-- FactContentUsage
CREATE TABLE IF NOT EXISTS mart.fact_content_usage (
    content_usage_id        VARCHAR(100) PRIMARY KEY,
    session_id              VARCHAR(100) REFERENCES mart.fact_session(session_id),
    content_id              VARCHAR(50) REFERENCES mart.dim_content(content_id),
    platform_id             VARCHAR(20) REFERENCES mart.dim_platform(platform_id),
    date_key                INTEGER REFERENCES mart.dim_date(date_key),
    time_spent_minutes      INTEGER NOT NULL DEFAULT 0,
    completion_status       VARCHAR(20),
    event_fingerprint       VARCHAR(64),
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- FactAIUsage
CREATE TABLE IF NOT EXISTS mart.fact_ai_usage (
    ai_usage_id             VARCHAR(100) PRIMARY KEY,
    session_id              VARCHAR(100) REFERENCES mart.fact_session(session_id),
    ai_service_id           VARCHAR(20) REFERENCES mart.dim_ai_service(ai_service_id),
    subject_id              VARCHAR(20) REFERENCES mart.dim_subject(subject_id),
    date_key                INTEGER REFERENCES mart.dim_date(date_key),
    query_count             INTEGER NOT NULL DEFAULT 0,
    time_spent_minutes      INTEGER NOT NULL DEFAULT 0,
    query_type              VARCHAR(50),
    event_fingerprint       VARCHAR(64),
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- FactAssessmentAttempt
CREATE TABLE IF NOT EXISTS mart.fact_assessment_attempt (
    attempt_id              VARCHAR(100) PRIMARY KEY,
    student_id              VARCHAR(50) REFERENCES mart.dim_student(student_id),
    content_id              VARCHAR(50) REFERENCES mart.dim_content(content_id),
    subject_id              VARCHAR(20) REFERENCES mart.dim_subject(subject_id),
    date_key                INTEGER REFERENCES mart.dim_date(date_key),
    score                   NUMERIC(5,2) CHECK (score BETWEEN 0 AND 100),
    attempt_number          SMALLINT NOT NULL DEFAULT 1,
    completion_status       VARCHAR(20),
    time_spent_minutes      INTEGER,
    event_fingerprint       VARCHAR(64),
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- FactSchoolDailySummary
CREATE TABLE IF NOT EXISTS mart.fact_school_daily_summary (
    school_id               VARCHAR(20) REFERENCES mart.dim_school(school_id),
    date_key                INTEGER REFERENCES mart.dim_date(date_key),
    active_students         INTEGER NOT NULL DEFAULT 0,
    active_teachers         INTEGER NOT NULL DEFAULT 0,
    total_sessions          INTEGER NOT NULL DEFAULT 0,
    total_learning_minutes  INTEGER NOT NULL DEFAULT 0,
    total_ai_queries        INTEGER NOT NULL DEFAULT 0,
    total_content_accesses  INTEGER NOT NULL DEFAULT 0,
    offline_sessions        INTEGER NOT NULL DEFAULT 0,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (school_id, date_key)
);

-- FactDeviceUsage
CREATE TABLE IF NOT EXISTS mart.fact_device_usage (
    device_usage_id         VARCHAR(100) PRIMARY KEY,
    device_id               VARCHAR(50) REFERENCES mart.dim_device(device_id),
    school_id               VARCHAR(20) REFERENCES mart.dim_school(school_id),
    date_key                INTEGER REFERENCES mart.dim_date(date_key),
    total_usage_minutes     INTEGER NOT NULL DEFAULT 0,
    session_count           INTEGER NOT NULL DEFAULT 0,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- FactPortalJob
CREATE TABLE IF NOT EXISTS mart.fact_portal_job (
    portal_job_id           VARCHAR(100) PRIMARY KEY,
    school_id               VARCHAR(20) REFERENCES mart.dim_school(school_id),
    job_type                VARCHAR(50),
    status                  VARCHAR(20),
    started_at              TIMESTAMPTZ,
    completed_at            TIMESTAMPTZ,
    error_message           TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- FactSyncHealth
CREATE TABLE IF NOT EXISTS mart.fact_sync_health (
    sync_health_id          VARCHAR(100) PRIMARY KEY,
    device_id               VARCHAR(50) REFERENCES mart.dim_device(device_id),
    school_id               VARCHAR(20) REFERENCES mart.dim_school(school_id),
    date_key                INTEGER REFERENCES mart.dim_date(date_key),
    status                  VARCHAR(20),
    records_synced          INTEGER NOT NULL DEFAULT 0,
    sync_duration_secs      INTEGER,
    synced_at               TIMESTAMPTZ,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);
