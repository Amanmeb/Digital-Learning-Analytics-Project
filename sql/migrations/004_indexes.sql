-- Migration 004
-- Performance indexes
-- CDLAID Analytics Platform

-- FactSession indexes
CREATE INDEX IF NOT EXISTS idx_fact_session_student
    ON mart.fact_session(student_id);
CREATE INDEX IF NOT EXISTS idx_fact_session_school
    ON mart.fact_session(school_id);
CREATE INDEX IF NOT EXISTS idx_fact_session_date
    ON mart.fact_session(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_session_platform
    ON mart.fact_session(platform_id);
CREATE INDEX IF NOT EXISTS idx_fact_session_fingerprint
    ON mart.fact_session(event_fingerprint);

-- FactTeacherSession indexes
CREATE INDEX IF NOT EXISTS idx_teacher_session_teacher
    ON mart.fact_teacher_session(teacher_id);
CREATE INDEX IF NOT EXISTS idx_teacher_session_school
    ON mart.fact_teacher_session(school_id);
CREATE INDEX IF NOT EXISTS idx_teacher_session_date
    ON mart.fact_teacher_session(date_key);

-- FactContentUsage indexes
CREATE INDEX IF NOT EXISTS idx_content_usage_session
    ON mart.fact_content_usage(session_id);
CREATE INDEX IF NOT EXISTS idx_content_usage_content
    ON mart.fact_content_usage(content_id);
CREATE INDEX IF NOT EXISTS idx_content_usage_date
    ON mart.fact_content_usage(date_key);
CREATE INDEX IF NOT EXISTS idx_content_usage_fingerprint
    ON mart.fact_content_usage(event_fingerprint);

-- FactAIUsage indexes
CREATE INDEX IF NOT EXISTS idx_ai_usage_session
    ON mart.fact_ai_usage(session_id);
CREATE INDEX IF NOT EXISTS idx_ai_usage_date
    ON mart.fact_ai_usage(date_key);
CREATE INDEX IF NOT EXISTS idx_ai_usage_subject
    ON mart.fact_ai_usage(subject_id);

-- FactAssessmentAttempt indexes
CREATE INDEX IF NOT EXISTS idx_assessment_student
    ON mart.fact_assessment_attempt(student_id);
CREATE INDEX IF NOT EXISTS idx_assessment_date
    ON mart.fact_assessment_attempt(date_key);
CREATE INDEX IF NOT EXISTS idx_assessment_content
    ON mart.fact_assessment_attempt(content_id);
CREATE INDEX IF NOT EXISTS idx_assessment_subject
    ON mart.fact_assessment_attempt(subject_id);

-- FactSchoolDailySummary indexes
CREATE INDEX IF NOT EXISTS idx_school_daily_date
    ON mart.fact_school_daily_summary(date_key);
CREATE INDEX IF NOT EXISTS idx_school_daily_school
    ON mart.fact_school_daily_summary(school_id);

-- FactSyncHealth indexes
CREATE INDEX IF NOT EXISTS idx_sync_health_school
    ON mart.fact_sync_health(school_id);
CREATE INDEX IF NOT EXISTS idx_sync_health_date
    ON mart.fact_sync_health(date_key);
CREATE INDEX IF NOT EXISTS idx_sync_health_status
    ON mart.fact_sync_health(status);

-- DimStudent indexes
CREATE INDEX IF NOT EXISTS idx_dim_student_school
    ON mart.dim_student(school_id);
CREATE INDEX IF NOT EXISTS idx_dim_student_grade
    ON mart.dim_student(grade_id);
CREATE INDEX IF NOT EXISTS idx_dim_student_active
    ON mart.dim_student(is_active);

-- DimSchool indexes
CREATE INDEX IF NOT EXISTS idx_dim_school_region
    ON mart.dim_school(region_id);
CREATE INDEX IF NOT EXISTS idx_dim_school_active
    ON mart.dim_school(is_active);

-- DimContent indexes
CREATE INDEX IF NOT EXISTS idx_dim_content_subject
    ON mart.dim_content(subject_id);
CREATE INDEX IF NOT EXISTS idx_dim_content_grade
    ON mart.dim_content(grade_id);
CREATE INDEX IF NOT EXISTS idx_dim_content_provider
    ON mart.dim_content(provider_id);
CREATE INDEX IF NOT EXISTS idx_dim_content_active
    ON mart.dim_content(is_active);
