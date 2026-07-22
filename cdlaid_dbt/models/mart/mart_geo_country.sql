-- Mart model for the country-level geo-rollup dashboard
-- One row per country, aggregating all regions and schools under it
-- map_latitude/map_longitude computed dynamically from all schools in
-- the country, same approach as mart_geo_region

select
    country_geo_id,
    country_name,
    count(distinct region_geo_id)                       as region_count,
    count(distinct school_id)                            as school_count,
    sum(registered_students)                             as registered_students,
    sum(active_students)                                 as active_students,
    sum(total_sessions)                                  as total_sessions,
    round(sum(total_learning_hours), 2)                 as total_learning_hours,
    round(avg(active_rate_pct), 2)                       as avg_active_rate_pct,
    round(avg(offline_usage_pct), 2)                     as avg_offline_usage_pct,
    round(avg(ai_adoption_rate_pct), 2)                  as avg_ai_adoption_rate_pct,
    max(last_active_date)                                as last_active_date,
    round(avg(latitude), 6)                              as map_latitude,
    round(avg(longitude), 6)                             as map_longitude,
    current_timestamp                                    as refreshed_at
from {{ ref("core_school_geo") }}
where country_geo_id is not null
group by country_geo_id, country_name