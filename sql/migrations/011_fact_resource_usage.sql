-- Migration 011
-- New fact table for device-tracking activity (apps, sites, books, idle, AI)
-- Separate from fact_content_usage, which stays tied to dim_content
-- (curated curriculum content). This table ties to dim_resource_catalog.
-- Additive only -- no existing table or column touched.

CREATE TABLE IF NOT EXISTS mart.fact_resource_usage (
    resource_usage_id   VARCHAR(100) PRIMARY KEY,
    session_id          VARCHAR(100),
    resource_id         VARCHAR(50),
    activity_type       VARCHAR(20) NOT NULL,
    date_key            INTEGER,
    start_time          TIMESTAMPTZ,
    end_time            TIMESTAMPTZ,
    duration_seconds    INTEGER NOT NULL DEFAULT 0,
    ai_service_id       VARCHAR(20),
    ai_query_count      INTEGER,
    event_fingerprint   VARCHAR(64),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT fact_resource_usage_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES mart.fact_session(session_id),
    CONSTRAINT fact_resource_usage_resource_id_fkey
        FOREIGN KEY (resource_id) REFERENCES mart.dim_resource_catalog(resource_id),
    CONSTRAINT fact_resource_usage_date_key_fkey
        FOREIGN KEY (date_key) REFERENCES mart.dim_date(date_key),
    CONSTRAINT fact_resource_usage_ai_service_id_fkey
        FOREIGN KEY (ai_service_id) REFERENCES mart.dim_ai_service(ai_service_id),
    CONSTRAINT fact_resource_usage_activity_type_check
        CHECK (activity_type IN ('app', 'site', 'book', 'idle', 'ai'))
);

CREATE INDEX IF NOT EXISTS idx_resource_usage_session ON mart.fact_resource_usage(session_id);
CREATE INDEX IF NOT EXISTS idx_resource_usage_resource ON mart.fact_resource_usage(resource_id);
CREATE INDEX IF NOT EXISTS idx_resource_usage_date ON mart.fact_resource_usage(date_key);
CREATE INDEX IF NOT EXISTS idx_resource_usage_fingerprint ON mart.fact_resource_usage(event_fingerprint);