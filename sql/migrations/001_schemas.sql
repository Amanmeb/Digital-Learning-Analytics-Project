-- Migration 001
-- Create database role and schema layers
-- CDLAID Analytics Platform

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_roles
        WHERE rolname = 'cdlaid_user'
    ) THEN
        CREATE ROLE cdlaid_user LOGIN PASSWORD 'changeme';
    END IF;
END
$$;

CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS ops;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS mart;

COMMENT ON SCHEMA auth IS 'Application authentication and user accounts';
COMMENT ON SCHEMA raw  IS 'Exact xAPI ingest -- unmodified';
COMMENT ON SCHEMA ops  IS 'Deduplicated, validated, cleaned';
COMMENT ON SCHEMA core IS 'Business logic and KPI calculations';
COMMENT ON SCHEMA mart IS 'Pre-aggregated -- dashboard ready';
