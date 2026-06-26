-- Migration 012
-- Student authentication table and class dimension
-- student_auth lives in ops schema, not mart, so password/PIN hashes are
-- never exposed to Superset or any BI/dashboard role
-- Additive only -- no existing table or column touched

CREATE TABLE IF NOT EXISTS mart.dim_class (
    class_id     VARCHAR(50) PRIMARY KEY,
    school_id    VARCHAR(20) NOT NULL,
    grade_id     VARCHAR(10),
    class_name   VARCHAR(100) NOT NULL,
    teacher_id   VARCHAR(50),
    is_active    BOOLEAN NOT NULL DEFAULT true,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT dim_class_school_id_fkey
        FOREIGN KEY (school_id) REFERENCES mart.dim_school(school_id),
    CONSTRAINT dim_class_grade_id_fkey
        FOREIGN KEY (grade_id) REFERENCES mart.dim_grade(grade_id),
    CONSTRAINT dim_class_teacher_id_fkey
        FOREIGN KEY (teacher_id) REFERENCES mart.dim_teacher(teacher_id)
);

CREATE INDEX IF NOT EXISTS idx_dim_class_school ON mart.dim_class(school_id);

CREATE TABLE IF NOT EXISTS ops.student_auth (
    student_id           VARCHAR(50) PRIMARY KEY,
    full_name            VARCHAR(200) NOT NULL,
    class_id             VARCHAR(50),
    id_type              VARCHAR(20) NOT NULL DEFAULT 'password',
    password_hash        VARCHAR(255),
    pin_hash             VARCHAR(255),
    language_preference  VARCHAR(20) NOT NULL DEFAULT 'English',
    country_code         VARCHAR(10) NOT NULL DEFAULT 'ET',
    geo_id               VARCHAR(50),
    enrollment_date      DATE,
    graduation_status    VARCHAR(20) NOT NULL DEFAULT 'active',
    failed_login_count   INTEGER NOT NULL DEFAULT 0,
    is_locked            BOOLEAN NOT NULL DEFAULT false,
    created_at           TIMESTAMPTZ DEFAULT NOW(),
    updated_at           TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT student_auth_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES mart.dim_student(student_id),
    CONSTRAINT student_auth_class_id_fkey
        FOREIGN KEY (class_id) REFERENCES mart.dim_class(class_id),
    CONSTRAINT student_auth_geo_id_fkey
        FOREIGN KEY (geo_id) REFERENCES mart.dim_geo_node(geo_id),
    CONSTRAINT student_auth_id_type_check
        CHECK (id_type IN ('password', 'pin')),
    CONSTRAINT student_auth_graduation_status_check
        CHECK (graduation_status IN ('active', 'graduated', 'transferred', 'dropped_out'))
);