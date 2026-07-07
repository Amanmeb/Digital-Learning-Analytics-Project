CREATE TABLE IF NOT EXISTS mart.fact_sync_health (

    sync_health_id TEXT PRIMARY KEY,

    device_id TEXT NOT NULL,

    school_id TEXT NOT NULL,

    date_key INTEGER NOT NULL,

    status TEXT NOT NULL,

    records_synced INTEGER NOT NULL DEFAULT 0,

    sync_duration_secs INTEGER,

    created_at TIMESTAMPTZ DEFAULT now()

);