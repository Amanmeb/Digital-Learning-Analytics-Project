-- Mart model for the region-level geo-rollup dashboard
-- One row per region, aggregating all schools under it
-- map_latitude/map_longitude give a dynamic map center point for the
-- region -- computed from its own schools rather than a fixed value,
-- so it stays accurate as schools are added, removed, or relocated

select
    region_geo_id,
    region_name,
    country_geo_id,
    country_name,
    count(distinct school_id)                          as school_count,
    sum(registered_students)                            as registered_students,
    sum(active_students)                                as active_students,
    sum(total_sessions)                                 as total_sessions,
    round(sum(total_learning_hours), 2)                as total_learning_hours,
    round(avg(active_rate_pct), 2)                      as avg_active_rate_pct,
    round(avg(offline_usage_pct), 2)                    as avg_offline_usage_pct,
    round(avg(ai_adoption_rate_pct), 2)                 as avg_ai_adoption_rate_pct,
    max(last_active_date)                               as last_active_date,
    round(avg(latitude), 6)                             as map_latitude,
    round(avg(longitude), 6)                            as map_longitude,
    current_timestamp                                   as refreshed_at
from {{ ref("core_school_geo") }}
where region_geo_id is not null
group by region_geo_id, region_name, country_geo_id, country_name