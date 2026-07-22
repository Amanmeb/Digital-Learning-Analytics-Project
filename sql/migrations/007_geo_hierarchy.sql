-- Migration 007
-- Geo hierarchy tables for global multi-country deployment
-- Additive only -- does not touch dim_region, region_id, or existing RLS

CREATE TABLE IF NOT EXISTS mart.dim_geo_level_config (
    country_code   VARCHAR(10) NOT NULL,
    level_number   SMALLINT NOT NULL,
    level_name     VARCHAR(50) NOT NULL,
    PRIMARY KEY (country_code, level_number)
);

CREATE TABLE IF NOT EXISTS mart.dim_geo_node (
    geo_id         VARCHAR(50) PRIMARY KEY,
    parent_geo_id  VARCHAR(50),
    country_code   VARCHAR(10) NOT NULL,
    level_number   SMALLINT NOT NULL,
    node_name      VARCHAR(200) NOT NULL,
    node_code      VARCHAR(50),
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT dim_geo_node_parent_fkey
        FOREIGN KEY (parent_geo_id) REFERENCES mart.dim_geo_node(geo_id)
);

CREATE INDEX IF NOT EXISTS idx_geo_node_parent ON mart.dim_geo_node(parent_geo_id);
CREATE INDEX IF NOT EXISTS idx_geo_node_country ON mart.dim_geo_node(country_code);
CREATE INDEX IF NOT EXISTS idx_geo_node_level ON mart.dim_geo_node(level_number);

INSERT INTO mart.dim_geo_level_config (country_code, level_number, level_name) VALUES
    ('ET', 1, 'Country'),
    ('ET', 2, 'Region'),
    ('ET', 3, 'Woreda')
ON CONFLICT DO NOTHING;

INSERT INTO mart.dim_geo_node (geo_id, parent_geo_id, country_code, level_number, node_name, node_code)
VALUES ('GEO-ET', NULL, 'ET', 1, 'Ethiopia', 'ET')
ON CONFLICT (geo_id) DO NOTHING;

-- node_code preserves the old region_id so the backfill below can match on it
INSERT INTO mart.dim_geo_node (geo_id, parent_geo_id, country_code, level_number, node_name, node_code)
SELECT
    'GEO-ET-' || r.region_id,
    'GEO-ET',
    'ET',
    2,
    r.region_name,
    r.region_id
FROM mart.dim_region r
ON CONFLICT (geo_id) DO NOTHING;

ALTER TABLE mart.dim_school ADD COLUMN IF NOT EXISTS geo_id VARCHAR(50);
ALTER TABLE mart.dim_content_provider ADD COLUMN IF NOT EXISTS geo_id VARCHAR(50);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'dim_school_geo_id_fkey'
    ) THEN
        ALTER TABLE mart.dim_school
            ADD CONSTRAINT dim_school_geo_id_fkey
            FOREIGN KEY (geo_id) REFERENCES mart.dim_geo_node(geo_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'dim_content_provider_geo_id_fkey'
    ) THEN
        ALTER TABLE mart.dim_content_provider
            ADD CONSTRAINT dim_content_provider_geo_id_fkey
            FOREIGN KEY (geo_id) REFERENCES mart.dim_geo_node(geo_id);
    END IF;
END $$;

UPDATE mart.dim_school s
SET geo_id = g.geo_id
FROM mart.dim_geo_node g
WHERE g.node_code = s.region_id AND g.level_number = 2 AND s.geo_id IS NULL;

UPDATE mart.dim_content_provider cp
SET geo_id = g.geo_id
FROM mart.dim_geo_node g
WHERE g.node_code = cp.region_id AND g.level_number = 2 AND cp.geo_id IS NULL;