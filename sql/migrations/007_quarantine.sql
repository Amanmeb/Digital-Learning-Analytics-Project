-- Migration 007
-- Quarantine table for malformed ingest records
-- Records that fail validation or FK checks land here instead of being dropped.

CREATE TABLE IF NOT EXISTS raw.quarantine (
    quarantine_id       BIGSERIAL PRIMARY KEY,
    table_name          VARCHAR(100) NOT NULL,
    raw_payload         JSONB NOT NULL,
    rejection_reason    TEXT NOT NULL,
    received_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quarantine_table
    ON raw.quarantine(table_name);

CREATE INDEX IF NOT EXISTS idx_quarantine_received
    ON raw.quarantine(received_at);
