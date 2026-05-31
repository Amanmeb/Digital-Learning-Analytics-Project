-- Migration 002
-- All 16 dimension tables
-- CDLAID Analytics Platform

-- DimDate
CREATE TABLE IF NOT EXISTS mart.dim_date (
    date_key        INTEGER PRIMARY KEY,
    full_date       DATE NOT NULL,
    day             SMALLINT NOT NULL,
    month           VARCHAR(10) NOT NULL,
    month_number    SMALLINT NOT NULL,
    quarter         VARCHAR(2) NOT NULL,
    year            SMALLINT NOT NULL,
    week_number     SMALLINT NOT NULL,
    day_of_week     VARCHAR(10) NOT NULL,
    academic_term   VARCHAR(10),
    is_weekend      BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at  TIMESTAMP NULL
);

-- DimRegion
CREATE TABLE IF NOT EXISTS mart.dim_region (
    region_id       VARCHAR(20) PRIMARY KEY,
    region_name     VARCHAR(100) NOT NULL,
    country         VARCHAR(100) NOT NULL DEFAULT 'Ethiopia',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at  TIMESTAMP NULL
);

-- DimSchool
CREATE TABLE IF NOT EXISTS mart.dim_school (
    school_id               VARCHAR(20) PRIMARY KEY,
    school_name             VARCHAR(200) NOT NULL,
    region_id               VARCHAR(20) REFERENCES mart.dim_region(region_id),
    zone                    VARCHAR(100),
    city                    VARCHAR(100),
    latitude                NUMERIC(9,6),
    longitude               NUMERIC(9,6),
    school_type             VARCHAR(50),
    education_level         VARCHAR(20),
    school_age_years        SMALLINT,
    last_sync_date          DATE,
    sync_frequency_days     SMALLINT DEFAULT 1,
    total_students          INTEGER,
    total_male              INTEGER,
    total_female            INTEGER,
    total_sne               INTEGER,
    total_teachers          INTEGER,
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at          TIMESTAMP NULL,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- DimGrade
CREATE TABLE IF NOT EXISTS mart.dim_grade (
    grade_id        VARCHAR(10) PRIMARY KEY,
    grade_level     SMALLINT NOT NULL,
    grade_label     VARCHAR(20) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at  TIMESTAMP NULL
);

-- DimSubject
CREATE TABLE IF NOT EXISTS mart.dim_subject (
    subject_id      VARCHAR(20) PRIMARY KEY,
    subject_name    VARCHAR(100) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at  TIMESTAMP NULL
);

-- DimLanguage
CREATE TABLE IF NOT EXISTS mart.dim_language (
    language_id     VARCHAR(20) PRIMARY KEY,
    language_name   VARCHAR(100) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at  TIMESTAMP NULL
);

-- DimContentType
CREATE TABLE IF NOT EXISTS mart.dim_content_type (
    content_type_id     VARCHAR(20) PRIMARY KEY,
    content_type_name   VARCHAR(50) NOT NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at      TIMESTAMP NULL
);

-- DimContentProvider
CREATE TABLE IF NOT EXISTS mart.dim_content_provider (
    provider_id         VARCHAR(20) PRIMARY KEY,
    provider_name       VARCHAR(200) NOT NULL,
    provider_type       VARCHAR(30),
    provider_level      VARCHAR(20),
    region_id           VARCHAR(20) REFERENCES mart.dim_region(region_id),
    country             VARCHAR(100) DEFAULT 'Ethiopia',
    is_content_owner    BOOLEAN DEFAULT FALSE,
    is_funder           BOOLEAN DEFAULT FALSE,
    is_distributor      BOOLEAN DEFAULT FALSE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at      TIMESTAMP NULL
);

-- DimContent
CREATE TABLE IF NOT EXISTS mart.dim_content (
    content_id          VARCHAR(50) PRIMARY KEY,
    content_name        VARCHAR(300) NOT NULL,
    content_type_id     VARCHAR(20) REFERENCES mart.dim_content_type(content_type_id),
    subject_id          VARCHAR(20) REFERENCES mart.dim_subject(subject_id),
    grade_id            VARCHAR(10) REFERENCES mart.dim_grade(grade_id),
    language_id         VARCHAR(20) REFERENCES mart.dim_language(language_id),
    provider_id         VARCHAR(20) REFERENCES mart.dim_content_provider(provider_id),
    is_offline          BOOLEAN DEFAULT TRUE,
    size_mb             NUMERIC(8,2),
    is_sne              BOOLEAN DEFAULT FALSE,
    last_updated_date   DATE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at      TIMESTAMP NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- DimPlatform
CREATE TABLE IF NOT EXISTS mart.dim_platform (
    platform_id         VARCHAR(20) PRIMARY KEY,
    platform_name       VARCHAR(100) NOT NULL,
    platform_type       VARCHAR(20) DEFAULT 'Offline',
    is_offline          BOOLEAN DEFAULT TRUE,
    tracking_method     VARCHAR(20),
    tracking_depth      VARCHAR(20),
    has_ai              BOOLEAN DEFAULT FALSE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at      TIMESTAMP NULL
);

-- DimDevice
CREATE TABLE IF NOT EXISTS mart.dim_device (
    device_id           VARCHAR(50) PRIMARY KEY,
    school_id           VARCHAR(20) REFERENCES mart.dim_school(school_id),
    device_type         VARCHAR(20),
    os                  VARCHAR(50),
    device_status       VARCHAR(20) DEFAULT 'Active',
    registered_at       TIMESTAMPTZ DEFAULT NOW(),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at      TIMESTAMP NULL
);

-- DimAIService
CREATE TABLE IF NOT EXISTS mart.dim_ai_service (
    ai_service_id       VARCHAR(20) PRIMARY KEY,
    ai_type             VARCHAR(50) NOT NULL,
    ai_scope            VARCHAR(50),
    ai_mode             VARCHAR(20),
    description         TEXT,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at      TIMESTAMP NULL
);

-- DimRole
CREATE TABLE IF NOT EXISTS mart.dim_role (
    role_id             VARCHAR(20) PRIMARY KEY,
    role_name           VARCHAR(50) NOT NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at      TIMESTAMP NULL
);

-- DimStudent
CREATE TABLE IF NOT EXISTS mart.dim_student (
    student_id          VARCHAR(50) PRIMARY KEY,
    school_id           VARCHAR(20) REFERENCES mart.dim_school(school_id),
    grade_id            VARCHAR(10) REFERENCES mart.dim_grade(grade_id),
    gender              VARCHAR(10),
    has_special_needs   BOOLEAN DEFAULT FALSE,
    special_need_type   VARCHAR(50),
    stream              VARCHAR(50),
    registration_date   DATE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at      TIMESTAMP NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- DimTeacher
CREATE TABLE IF NOT EXISTS mart.dim_teacher (
    teacher_id          VARCHAR(50) PRIMARY KEY,
    school_id           VARCHAR(20) REFERENCES mart.dim_school(school_id),
    gender              VARCHAR(10),
    education_level     VARCHAR(30),
    field_of_study      VARCHAR(100),
    role_id             VARCHAR(20) REFERENCES mart.dim_role(role_id),
    registration_date   DATE,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at      TIMESTAMP NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- DimProject
CREATE TABLE IF NOT EXISTS mart.dim_project (
    project_id          VARCHAR(20) PRIMARY KEY,
    project_name        VARCHAR(200) NOT NULL,
    start_date          DATE,
    end_date            DATE,
    funder              VARCHAR(200),
    description         TEXT,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at      TIMESTAMP NULL
);

-- DimResourceCatalog
CREATE TABLE IF NOT EXISTS mart.dim_resource_catalog (
    resource_id         VARCHAR(50) PRIMARY KEY,
    resource_name       VARCHAR(300) NOT NULL,
    resource_type       VARCHAR(50),
    source_id           VARCHAR(20) REFERENCES mart.dim_content_provider(provider_id),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    deactivated_at      TIMESTAMP NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
