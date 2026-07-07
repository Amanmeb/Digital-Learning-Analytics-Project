CREATE TABLE IF NOT EXISTS mart.fact_device_usage (

    device_usage_id TEXT PRIMARY KEY,

    device_id TEXT NOT NULL,

    school_id TEXT NOT NULL,

    date_key INTEGER NOT NULL,

    total_usage_minutes INTEGER NOT NULL DEFAULT 0,

    session_count INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT now()

);