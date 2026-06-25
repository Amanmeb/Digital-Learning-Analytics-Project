-- Migration 008
-- Role scope settings, device and resource catalog extensions
-- Additive only -- no existing column, table, or RLS policy is altered

CREATE TABLE IF NOT EXISTS mart.role_scope_settings (
    role_id      VARCHAR(20) NOT NULL PRIMARY KEY,
    scope_type   VARCHAR(20) NOT NULL,
    is_default   BOOLEAN NOT NULL DEFAULT true,
    updated_at   TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT role_scope_settings_role_id_fkey
        FOREIGN KEY (role_id) REFERENCES mart.dim_role(role_id),
    CONSTRAINT role_scope_settings_scope_type_check
        CHECK (scope_type IN ('self', 'school', 'region', 'country', 'all'))
);

INSERT INTO mart.role_scope_settings (role_id, scope_type, is_default) VALUES
    ('ROL_STU',   'self',    true),
    ('ROL_TEA',   'self',    true),
    ('ROL_PRIN',  'school',  true),
    ('ROL_VPRIN', 'school',  true),
    ('ROL_DEPT',  'school',  true),
    ('ROL_ADM',   'school',  true),
    ('ROL_CURR',  'school',  true),
    ('ROL_ICT',   'school',  true),
    ('ROL_SNE',   'school',  true),
    ('ROL_REG',   'region',  true),
    ('ROL_PROG',  'country', true)
ON CONFLICT (role_id) DO NOTHING;

ALTER TABLE mart.dim_device ADD COLUMN IF NOT EXISTS device_name VARCHAR(200);
ALTER TABLE mart.dim_device ADD COLUMN IF NOT EXISTS assigned_location VARCHAR(100);
ALTER TABLE mart.dim_device ADD COLUMN IF NOT EXISTS health_score SMALLINT;
ALTER TABLE mart.dim_device ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ;
ALTER TABLE mart.dim_device ADD COLUMN IF NOT EXISTS bandwidth_used_mb_daily NUMERIC(10,2) DEFAULT 0;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'dim_device_health_score_check'
    ) THEN
        ALTER TABLE mart.dim_device
            ADD CONSTRAINT dim_device_health_score_check
            CHECK (health_score IS NULL OR (health_score >= 0 AND health_score <= 100));
    END IF;
END $$;

ALTER TABLE mart.dim_resource_catalog ADD COLUMN IF NOT EXISTS is_educational BOOLEAN;
ALTER TABLE mart.dim_resource_catalog ADD COLUMN IF NOT EXISTS subject_id VARCHAR(20);
ALTER TABLE mart.dim_resource_catalog ADD COLUMN IF NOT EXISTS discovery_method VARCHAR(20) DEFAULT 'manual';
ALTER TABLE mart.dim_resource_catalog ADD COLUMN IF NOT EXISTS is_reviewed BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE mart.dim_resource_catalog ADD COLUMN IF NOT EXISTS risk_flag VARCHAR(20) DEFAULT 'unknown';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'dim_resource_catalog_subject_id_fkey'
    ) THEN
        ALTER TABLE mart.dim_resource_catalog
            ADD CONSTRAINT dim_resource_catalog_subject_id_fkey
            FOREIGN KEY (subject_id) REFERENCES mart.dim_subject(subject_id);
    END IF;
END $$;