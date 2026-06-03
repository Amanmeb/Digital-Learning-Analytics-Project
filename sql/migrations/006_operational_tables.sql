-- Migration 006
-- Operational tables
-- CDLAID Analytics Platform

-- Raw xAPI statements table
-- Receives exact xAPI statements from sync agent via FastAPI
-- Never modified after insert -- source of truth for all processing
CREATE TABLE IF NOT EXISTS raw.xapi_statements (
    statement_id        VARCHAR(100) PRIMARY KEY,
    server_id           VARCHAR(50) NOT NULL,
    school_id           VARCHAR(20),
    actor               JSONB NOT NULL,
    verb                JSONB NOT NULL,
    object              JSONB NOT NULL,
    result              JSONB,
    context             JSONB,
    timestamp           TIMESTAMPTZ NOT NULL,
    stored              TIMESTAMPTZ DEFAULT NOW(),
    processed           BOOLEAN DEFAULT FALSE,
    process_error       TEXT,
    event_fingerprint   VARCHAR(64)
);

CREATE INDEX IF NOT EXISTS idx_xapi_server
    ON raw.xapi_statements(server_id);
CREATE INDEX IF NOT EXISTS idx_xapi_timestamp
    ON raw.xapi_statements(timestamp);
CREATE INDEX IF NOT EXISTS idx_xapi_processed
    ON raw.xapi_statements(processed);
CREATE INDEX IF NOT EXISTS idx_xapi_fingerprint
    ON raw.xapi_statements(event_fingerprint);

-- Sync log
-- Records every upload batch from every school server
-- Used for sync health KPI and backlog alert calculations
CREATE TABLE IF NOT EXISTS ops.sync_log (
    sync_id                 VARCHAR(100) PRIMARY KEY,
    server_id               VARCHAR(50) NOT NULL,
    school_id               VARCHAR(20),
    request_id              VARCHAR(100),
    statements_received     INTEGER NOT NULL DEFAULT 0,
    statements_inserted     INTEGER NOT NULL DEFAULT 0,
    statements_rejected     INTEGER NOT NULL DEFAULT 0,
    statements_duplicate    INTEGER NOT NULL DEFAULT 0,
    import_source           VARCHAR(20) DEFAULT 'sync_agent',
    status                  VARCHAR(20),
    error_message           TEXT,
    synced_at               TIMESTAMPTZ DEFAULT NOW()
);

-- Manual import log
-- Records every CSV and Excel import via admin panel
-- Used for data quality dashboard in Step 10
CREATE TABLE IF NOT EXISTS ops.manual_import_log (
    import_id           BIGSERIAL PRIMARY KEY,
    school_id           VARCHAR(20),
    imported_by         VARCHAR(100),
    file_name           VARCHAR(300),
    file_type           VARCHAR(10),
    data_type           VARCHAR(50),
    rows_received       INTEGER NOT NULL DEFAULT 0,
    rows_inserted       INTEGER NOT NULL DEFAULT 0,
    rows_duplicate      INTEGER NOT NULL DEFAULT 0,
    rows_invalid        INTEGER NOT NULL DEFAULT 0,
    import_source       VARCHAR(20) DEFAULT 'manual_csv',
    imported_at         TIMESTAMPTZ DEFAULT NOW()
);

-- Audit log
-- Records all sensitive actions for security and compliance
-- Data retention: 3 years per build plan
CREATE TABLE IF NOT EXISTS ops.audit_log (
    audit_id            BIGSERIAL PRIMARY KEY,
    event_time          TIMESTAMPTZ DEFAULT NOW(),
    user_name           VARCHAR(100) NOT NULL,
    role_name           VARCHAR(50),
    school_id           VARCHAR(20),
    action              VARCHAR(50) NOT NULL,
    table_name          VARCHAR(100),
    record_count        INTEGER,
    ip_address          INET,
    request_id          VARCHAR(100),
    details             TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_user
    ON ops.audit_log(user_name);
CREATE INDEX IF NOT EXISTS idx_audit_time
    ON ops.audit_log(event_time);
CREATE INDEX IF NOT EXISTS idx_audit_school
    ON ops.audit_log(school_id);

-- System log
-- Records all structured application logs from FastAPI and sync agent
-- Used for pipeline health dashboard in Step 10
CREATE TABLE IF NOT EXISTS ops.system_log (
    log_id              BIGSERIAL PRIMARY KEY,
    log_time            TIMESTAMPTZ DEFAULT NOW(),
    log_level           VARCHAR(10) NOT NULL,
    component           VARCHAR(50),
    school_id           VARCHAR(20),
    event               VARCHAR(200),
    duration_ms         INTEGER,
    request_id          VARCHAR(100),
    details             TEXT
);

CREATE INDEX IF NOT EXISTS idx_system_log_time
    ON ops.system_log(log_time);
CREATE INDEX IF NOT EXISTS idx_system_log_level
    ON ops.system_log(log_level);
CREATE INDEX IF NOT EXISTS idx_system_log_component
    ON ops.system_log(component);

-- Translations table
-- Stores KPI label translations for multi-language dashboard support
-- English is primary -- other languages added via admin panel
CREATE TABLE IF NOT EXISTS ops.translations (
    translation_key     VARCHAR(100) NOT NULL,
    language_code       VARCHAR(10) NOT NULL,
    translation_value   TEXT NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (translation_key, language_code)
);

-- English translations for all KPI labels
INSERT INTO ops.translations (translation_key, language_code, translation_value) VALUES
    ('kpi_total_students',              'en', 'Total Students'),
    ('kpi_active_students',             'en', 'Active Students'),
    ('kpi_active_schools',              'en', 'Active Schools'),
    ('kpi_total_sessions',              'en', 'Total Sessions'),
    ('kpi_learning_hours',              'en', 'Total Learning Hours'),
    ('kpi_ai_usage_rate',               'en', 'AI Usage Rate'),
    ('kpi_offline_usage',               'en', 'Offline Usage'),
    ('kpi_performance_index',           'en', 'Performance Index'),
    ('kpi_gender_parity',               'en', 'Gender Parity Index'),
    ('kpi_sne_participation',           'en', 'SNE Participation Rate'),
    ('kpi_sync_health',                 'en', 'Sync Health'),
    ('kpi_active_devices',              'en', 'Active Devices'),
    ('kpi_learning_engagement_index',   'en', 'Learning Engagement Index'),
    ('kpi_school_performance_index',    'en', 'School Performance Index'),
    ('kpi_student_achievement_index',   'en', 'Student Achievement Index'),
    ('kpi_ai_impact_index',             'en', 'AI Learning Impact Index'),
    ('kpi_retention_index',             'en', 'Retention and Re-engagement Index'),
    ('kpi_content_completion_rate',     'en', 'Content Completion Rate'),
    ('kpi_pass_rate',                   'en', 'Pass Rate'),
    ('kpi_mastery_rate',                'en', 'Mastery Rate'),
    ('kpi_score_improvement',           'en', 'Score Improvement Rate'),
    ('kpi_ai_adoption_rate',            'en', 'AI Adoption Rate'),
    ('kpi_first_week_activation',       'en', 'First Week Activation Rate'),
    ('kpi_content_staleness',           'en', 'Content Staleness Rate'),
    ('kpi_device_utilisation',          'en', 'Device Utilisation'),
    ('kpi_stale_schools',               'en', 'Stale Schools Count'),
    ('kpi_registration_coverage',       'en', 'Registration Coverage'),
    ('kpi_early_dropoff',               'en', 'Early Drop-off Rate'),
    ('kpi_late_dropoff',                'en', 'Late Drop-off Rate'),
    ('kpi_reengagement_rate',           'en', 'Re-engagement Rate')
ON CONFLICT DO NOTHING;

-- Settings table
-- All adjustable parameters for dashboards and KPI calculations
-- Tier A -- permanent change via admin panel
-- Tier B -- session only via dashboard filter
-- Tier C -- environment variable for infrastructure settings
CREATE TABLE IF NOT EXISTS ops.settings (
    setting_key         VARCHAR(100) NOT NULL,
    setting_value       VARCHAR(500) NOT NULL,
    setting_scope       VARCHAR(50) DEFAULT 'global',
    description         TEXT,
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (setting_key, setting_scope)
);

-- Default settings -- all adjustable via admin panel
INSERT INTO ops.settings (setting_key, setting_value, setting_scope, description) VALUES
    -- Dashboard display settings
    ('top_n_default',           '10',           'global', 'Default number of items in ranked charts'),
    ('chart_granularity',       'Monthly',      'global', 'Default chart time granularity'),
    ('date_range_default',      '30',           'global', 'Default date range in days for dashboards'),
    ('demo_mode',               'false',        'global', 'When true all IDs are anonymised in dashboards'),

    -- Brand colors
    ('primary_color',           '#81BC00',      'global', 'Brand primary green color'),
    ('secondary_color',         '#375C7A',      'global', 'Brand primary blue color'),
    ('accent_color',            '#943266',      'global', 'Brand secondary purple color'),

    -- Assessment thresholds
    ('pass_threshold',          '50',           'global', 'Minimum score to pass an assessment'),
    ('mastery_threshold',       '80',           'global', 'Minimum score to achieve mastery'),

    -- Adoption targets
    ('ai_adoption_target',      '30',           'global', 'Target AI adoption rate percentage'),

    -- Equity thresholds
    ('gender_parity_min',       '0.9',          'global', 'Minimum acceptable gender parity index'),
    ('gender_parity_max',       '1.1',          'global', 'Maximum acceptable gender parity index'),

    -- Content flags
    ('completion_flag',         '40',           'global', 'Completion rate below this is flagged'),
    ('content_stale_days',      '365',          'global', 'Days before content is considered stale'),

    -- School flags
    ('school_coverage_flag',    '50',           'global', 'Registration coverage below this is flagged'),
    ('school_performance_flag', '0.4',          'global', 'Performance index below this is flagged'),

    -- Session settings
    ('inactivity_cutoff_min',   '30',           'global', 'Minutes before session is considered ended'),
    ('first_week_days',         '7',            'global', 'Days for first week activation window'),

    -- Re-engagement
    ('reengagement_days',       '14',           'global', 'Days inactive before counted as lapsed'),

    -- Sync health
    ('sync_health_target',      '95',           'global', 'Target sync health percentage'),

    -- Composite KPI weights
    -- Stored as JSON strings -- read by dbt get_setting macro in Step 9
    -- All weights in each group must sum to 1.00
    ('learning_engagement_weights',
        '{"activity_participation":0.30,"session_duration":0.30,"content_completion":0.20,"ai_usage":0.20}',
        'global',
        'Composite weights for Learning Engagement Index -- must sum to 1.00'),

    ('school_performance_weights',
        '{"active_rate":0.25,"avg_score":0.25,"completion_rate":0.25,"ai_adoption":0.25}',
        'global',
        'Composite weights for School Performance Index -- must sum to 1.00'),

    ('student_achievement_weights',
        '{"avg_score":0.40,"pass_rate":0.30,"score_improvement":0.30}',
        'global',
        'Composite weights for Student Achievement Index -- must sum to 1.00'),

    ('ai_impact_weights',
        '{"frequency":0.25,"duration":0.25,"subject_coverage":0.25,"score_improvement":0.25}',
        'global',
        'Composite weights for AI Learning Impact Index -- must sum to 1.00'),

    ('retention_weights',
        '{"returning_users":0.40,"active_days":0.40,"reengagement":0.20}',
        'global',
        'Composite weights for Retention and Re-engagement Index -- must sum to 1.00')

ON CONFLICT DO NOTHING;