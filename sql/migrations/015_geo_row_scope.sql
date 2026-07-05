-- Migration 015
-- Adds a function to check whether a geo node (region, country, or any
-- level) overlaps with a user's assigned scope -- used by the second
-- RLS rule for geo-rollup datasets (mart_geo_region, mart_geo_country)
-- which have no school_id column and so cannot use schools_in_scope
-- directly. A row is visible if at least one school under the row's
-- own geo_id is also in the user's scope.

CREATE OR REPLACE FUNCTION mart.geo_row_in_scope(p_user_id INTEGER, p_row_geo_id VARCHAR(50))
RETURNS BOOLEAN AS $$
WITH RECURSIVE row_descendants AS (
    SELECT geo_id
    FROM mart.dim_geo_node
    WHERE geo_id = p_row_geo_id

    UNION ALL

    SELECT g.geo_id
    FROM mart.dim_geo_node g
    JOIN row_descendants d ON g.parent_geo_id = d.geo_id
)
SELECT EXISTS (
    SELECT 1
    FROM mart.dim_school s
    WHERE s.geo_id IN (SELECT geo_id FROM row_descendants)
      AND s.school_id IN (SELECT school_id FROM mart.schools_in_scope(p_user_id))
);
$$ LANGUAGE sql STABLE;