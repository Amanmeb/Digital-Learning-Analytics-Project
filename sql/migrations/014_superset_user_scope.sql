-- Migration 014
-- Adjustable, per-user row-level access control for Superset dashboards
-- Replaces the dead Postgres-native RLS from migration 005, which was
-- never actually enforced -- Superset connects as cdlaid_user, which
-- bypasses RLS entirely, and no code ever set the session variables
-- those policies depended on.
--
-- This table lets an admin assign any Superset user a geo scope
-- (country, region, zone, or woreda level -- any depth) or mark them
-- as full access. Editing a row here takes effect immediately, with
-- no code change or redeploy needed.

CREATE TABLE IF NOT EXISTS ops.superset_user_scope (
    superset_user_id  INTEGER PRIMARY KEY,
    geo_id             VARCHAR(50) REFERENCES mart.dim_geo_node(geo_id),
    is_all_access      BOOLEAN NOT NULL DEFAULT FALSE,
    notes              VARCHAR(200),
    updated_at         TIMESTAMPTZ DEFAULT NOW()
);

-- Returns every school_id under a given geo_id, at any depth below it.
-- Works regardless of whether geo_id is a country, region, zone, or
-- woreda node -- walks the hierarchy down recursively each time it is
-- called, so it stays correct as new levels or nodes are added.
CREATE OR REPLACE FUNCTION mart.schools_in_scope(p_user_id INTEGER)
RETURNS TABLE(school_id VARCHAR(20)) AS $$
WITH RECURSIVE descendants AS (
    SELECT geo_id
    FROM mart.dim_geo_node
    WHERE geo_id = (
        SELECT geo_id FROM ops.superset_user_scope
        WHERE superset_user_id = p_user_id
    )

    UNION ALL

    SELECT g.geo_id
    FROM mart.dim_geo_node g
    JOIN descendants d ON g.parent_geo_id = d.geo_id
)
SELECT s.school_id
FROM mart.dim_school s
WHERE
    (
        SELECT is_all_access FROM ops.superset_user_scope
        WHERE superset_user_id = p_user_id
    ) = TRUE
    OR s.geo_id IN (SELECT geo_id FROM descendants);
$$ LANGUAGE sql STABLE;