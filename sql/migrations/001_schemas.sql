-- Migration 001
-- Create four schema layers
-- CDLAID Analytics Platform

CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS ops;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS mart;

COMMENT ON SCHEMA raw  IS 'Exact xAPI ingest -- unmodified';
COMMENT ON SCHEMA ops  IS 'Deduplicated, validated, cleaned';
COMMENT ON SCHEMA core IS 'Business logic and KPI calculations';
COMMENT ON SCHEMA mart IS 'Pre-aggregated -- dashboard ready';
