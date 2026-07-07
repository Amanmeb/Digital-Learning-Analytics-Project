CREATE TABLE IF NOT EXISTS mart.fact_school_daily_summary (

    school_id                 TEXT NOT NULL,

    date_key                  INTEGER NOT NULL,

    active_students           INTEGER NOT NULL DEFAULT 0,

    active_teachers           INTEGER NOT NULL DEFAULT 0,

    total_sessions            INTEGER NOT NULL DEFAULT 0,

    total_learning_minutes    INTEGER NOT NULL DEFAULT 0,

    total_ai_queries          INTEGER NOT NULL DEFAULT 0,

    total_content_accesses    INTEGER NOT NULL DEFAULT 0,

    offline_sessions          INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT now(),

    PRIMARY KEY (school_id, date_key)

);