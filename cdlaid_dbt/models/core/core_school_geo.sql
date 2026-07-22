-- Core model joining school-level activity with the geo hierarchy
-- One row per active school -- feeds mart_geo_region and mart_geo_country
-- Latitude/longitude carried through for map-based dashboards
-- dim_school.geo_id points to the zone/sub-city level (level 3) --
-- this model walks up through parent_geo_id to reach region and country

with school_geo as (
    select
        s.school_id,
        s.school_name,
        s.school_type,
        s.geo_id                                    as zone_geo_id,
        s.latitude,
        s.longitude,
        s.total_students                            as registered_students,
        s.is_active
    from mart.dim_school s
    where s.is_active = true
      and s.geo_id is not null
),

zone_lookup as (
    select
        geo_id          as zone_geo_id,
        node_name       as zone_name,
        parent_geo_id   as region_geo_id
    from mart.dim_geo_node
    where level_number = 3
),

region_lookup as (
    select
        geo_id          as region_geo_id,
        node_name       as region_name,
        parent_geo_id   as country_geo_id
    from mart.dim_geo_node
    where level_number = 2
),

country_lookup as (
    select
        geo_id      as country_geo_id,
        node_name   as country_name
    from mart.dim_geo_node
    where level_number = 1
),

school_activity as (
    select
        school_id,
        sum(active_students)                            as total_active_students,
        sum(total_sessions)                             as total_sessions,
        round(sum(total_learning_minutes) / 60.0, 2)    as total_learning_hours,
        sum(offline_sessions)                            as total_offline_sessions,
        sum(students_used_ai)                            as total_students_used_ai,
        max(summary_date)                                as last_active_date
    from {{ ref("core_school_summary") }}
    group by school_id
)

select
    sg.school_id,
    sg.school_name,
    sg.school_type,
    sg.registered_students,
    sg.latitude,
    sg.longitude,
    sg.zone_geo_id,
    zl.zone_name,
    zl.region_geo_id,
    rl.region_name,
    rl.country_geo_id,
    cl.country_name,
    coalesce(sa.total_active_students, 0)     as active_students,
    coalesce(sa.total_sessions, 0)            as total_sessions,
    coalesce(sa.total_learning_hours, 0)      as total_learning_hours,
    coalesce(sa.total_offline_sessions, 0)    as offline_sessions,
    coalesce(sa.total_students_used_ai, 0)    as students_used_ai,
    sa.last_active_date,
    case
        when sg.registered_students > 0
        then round(coalesce(sa.total_active_students, 0)::numeric / sg.registered_students * 100, 2)
        else 0
    end                                        as active_rate_pct,
    case
        when coalesce(sa.total_sessions, 0) > 0
        then round(coalesce(sa.total_offline_sessions, 0)::numeric / sa.total_sessions * 100, 2)
        else 0
    end                                        as offline_usage_pct,
    case
        when coalesce(sa.total_active_students, 0) > 0
        then round(coalesce(sa.total_students_used_ai, 0)::numeric / sa.total_active_students * 100, 2)
        else 0
    end                                        as ai_adoption_rate_pct
from school_geo sg
left join zone_lookup zl on sg.zone_geo_id = zl.zone_geo_id
left join region_lookup rl on zl.region_geo_id = rl.region_geo_id
left join country_lookup cl on rl.country_geo_id = cl.country_geo_id
left join school_activity sa on sg.school_id = sa.school_id