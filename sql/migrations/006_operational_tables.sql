-- Migration 006
-- Operational tables
-- CDLAID Analytics Platform

-- Raw xAPI statements table
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
CREATE TABLE IF NOT EXISTS ops.translations (
    translation_key     VARCHAR(100) NOT NULL,
    language_code       VARCHAR(10) NOT NULL,
    translation_value   TEXT NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (translation_key, language_code)
);

-- Insert English translations for all KPI labels
INSERT INTO ops.translations (translation_key, language_code, translation_value) VALUES
    ('kpi_total_students',      'en', 'Total Students'),
    ('kpi_active_students',     'en', 'Active Students'),
    ('kpi_active_schools',      'en', 'Active Schools'),
    ('kpi_total_sessions',      'en', 'Total Sessions'),
    ('kpi_learning_hours',      'en', 'Total Learning Hours'),
    ('kpi_ai_usage_rate',       'en', 'AI Usage Rate'),
    ('kpi_offline_usage',       'en', 'Offline Usage'),
    ('kpi_performance_index',   'en', 'Performance Index'),
    ('kpi_gender_parity',       'en', 'Gender Parity Index'),
    ('kpi_sne_participation',   'en', 'SNE Participation Rate'),
    ('kpi_sync_health',         'en', 'Sync Health'),
    ('kpi_active_devices',      'en', 'Active Devices')
ON CONFLICT DO NOTHING;

-- Settings table
CREATE TABLE IF NOT EXISTS ops.settings (
    setting_key         VARCHAR(100) NOT NULL,
    setting_value       VARCHAR(500) NOT NULL,
    setting_scope       VARCHAR(50) DEFAULT 'global',
    description         TEXT,
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (setting_key, setting_scope)
);

-- Insert default settings
INSERT INTO ops.settings (setting_key, setting_value, setting_scope, description) VALUES
    ('top_n_default',           '10',       'global', 'Default number of items in ranked charts'),
    ('pass_threshold',          '50',       'global', 'Minimum score to pass an assessment'),
    ('mastery_threshold',       '80',       'global', 'Minimum score to achieve mastery'),
    ('ai_adoption_target',      '30',       'global', 'Target AI adoption rate percentage'),
    ('gender_parity_min',       '0.9',      'global', 'Minimum acceptable gender parity index'),
    ('gender_parity_max',       '1.1',      'global', 'Maximum acceptable gender parity index'),
    ('completion_flag',         '40',       'global', 'Completion rate below this is flagged'),
    ('school_coverage_flag',    '50',       'global', 'Registration coverage below this is flagged'),
    ('school_performance_flag', '0.4',      'global', 'Performance index below this is flagged'),
    ('inactivity_cutoff_min',   '30',       'global', 'Minutes before session is considered ended'),
    ('reengagement_days',       '14',       'global', 'Days inactive before counted as lapsed'),
    ('sync_health_target',      '95',       'global', 'Target sync health percentage'),
    ('content_stale_days',      '365',      'global', 'Days before content is considered stale'),
    ('first_week_days',         '7',        'global', 'Days for first week activation window'),
    ('date_range_default',      '30',       'global', 'Default date range in days for dashboards'),
    ('chart_granularity',       'Monthly',  'global', 'Default chart time granularity'),
    ('demo_mode',               'false',    'global', 'When true all IDs are anonymised in dashboards'),
    ('primary_color',           '#81BC00',  'global', 'Brand primary green color'),
    ('secondary_color',         '#375C7A',  'global', 'Brand primary blue color'),
    ('accent_color',            '#943266',  'global', 'Brand secondary purple color')
ON CONFLICT DO NOTHING;
