-- Migration 013
-- Adds Zone as level 3 in the geo hierarchy, correcting the previous
-- 3-level config which mislabeled zone data as woreda. Woreda becomes
-- level 4, and remains unseeded -- true woreda data is not yet available
-- and is a separate future step, not faked here.
-- Addis Ababa sub-cities occupy level 3 in place of a zone, since it is
-- a chartered city administration with no separate zone tier.

INSERT INTO mart.dim_geo_level_config (country_code, level_number, level_name) VALUES
    ('ET', 4, 'Woreda')
ON CONFLICT (country_code, level_number) DO NOTHING;

UPDATE mart.dim_geo_level_config
SET level_name = 'Zone'
WHERE country_code = 'ET' AND level_number = 3;

INSERT INTO mart.dim_geo_level_config (country_code, level_number, level_name) VALUES
    ('ET', 3, 'Zone')
ON CONFLICT (country_code, level_number) DO NOTHING;

-- Seed zone/sub-city nodes for every distinct zone value currently used
-- by an active school, parented to that school's region node
INSERT INTO mart.dim_geo_node (geo_id, parent_geo_id, country_code, level_number, node_name, node_code)
SELECT DISTINCT
    'GEO-ET-' || s.region_id || '-' || replace(upper(s.zone), ' ', '-'),
    g.geo_id,
    'ET',
    3,
    s.zone,
    s.zone
FROM mart.dim_school s
JOIN mart.dim_geo_node g
    ON g.node_code = s.region_id AND g.level_number = 2
WHERE s.zone IS NOT NULL
ON CONFLICT (geo_id) DO NOTHING;

-- Backfill dim_school.geo_id to point at the zone/sub-city level (3)
-- instead of the region level (2), now that zone data is real
UPDATE mart.dim_school s
SET geo_id = g.geo_id
FROM mart.dim_geo_node g
WHERE g.level_number = 3
  AND g.node_name = s.zone
  AND g.parent_geo_id = (
      SELECT geo_id FROM mart.dim_geo_node
      WHERE node_code = s.region_id AND level_number = 2
  );