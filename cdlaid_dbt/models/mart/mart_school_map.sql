-- Mart model for school geographic map
-- One row per school with location and KPI data
-- Used by the school map chart on Executive Overview and School Performance dashboards

with school_performance as (
    select
        school_id,
        sum(active_students)                            as total_active_students,
        sum(total_sessions)                             as total_sessions,
        round(sum(total_learning_minutes) / 60.0, 2)   as total_learning_hours,
        sum(offline_sessions)                           as total_offline_sessions,
        sum(students_used_ai)                           as total_students_used_ai,
        max(summary_date)                               as last_active_date
    from {{ ref("core_school_summary") }}
    group by school_id
),

school_scores as (
    select
        sp.school_id,
        sp.total_active_students,
        sp.total_sessions,
        sp.total_learning_hours,
        sp.last_active_date,
        case
            when sp.total_sessions > 0
            then round(sp.total_offline_sessions::numeric / sp.total_sessions * 100, 2)
            else 0
        end                                             as offline_usage_pct,
        case
            when sp.total_active_students > 0
            then round(sp.total_students_used_ai::numeric / sp.total_active_students * 100, 2)
            else 0
        end                                             as ai_adoption_rate_pct,
        case
            when coalesce(ds.total_students, 0) > 0
            then round(sp.total_active_students::numeric / ds.total_students * 100, 2)
            else 0
        end                                             as active_rate_pct,
        case
            when coalesce(ds.total_students, 0) > 0
                and sp.total_sessions > 0
            then round(
                (sp.total_active_students::numeric / greatest(ds.total_students, 1) * 0.6)
                + (least(sp.total_sessions::numeric / 100, 1) * 0.4)
            , 4)
            else 0
        end                                             as performance_index
    from school_performance sp
    join mart.dim_school ds on sp.school_id = ds.school_id
)

select
    ds.school_id,
    ds.school_name,
    ds.school_type,
    ds.city,
    ds.zone,
    r.region_name,
    ds.latitude,
    ds.longitude,
    ds.total_students                                   as registered_students,
    ds.total_male,
    ds.total_female,
    ds.total_sne,
    ds.total_teachers,
    ds.last_sync_date,
    ds.is_active,
    coalesce(sc.total_active_students, 0)               as active_students,
    coalesce(sc.total_sessions, 0)                      as total_sessions,
    coalesce(sc.total_learning_hours, 0)                as total_learning_hours,
    coalesce(sc.ai_adoption_rate_pct, 0)                as ai_adoption_rate_pct,
    coalesce(sc.offline_usage_pct, 0)                   as offline_usage_pct,
    coalesce(sc.active_rate_pct, 0)                     as active_rate_pct,
    coalesce(sc.performance_index, 0)                   as performance_index,
    coalesce(sc.last_active_date, null)                 as last_active_date,
    case
        when coalesce(sc.performance_index, 0) >= 0.7 then 'High'
        when coalesce(sc.performance_index, 0) >= 0.4 then 'Medium'
        when sc.school_id is not null then 'Low'
        else 'No Data'
    end                                                 as performance_tier,
    current_timestamp                                   as refreshed_at
from mart.dim_school ds
left join mart.dim_region r on ds.region_id = r.region_id
left join school_scores sc on ds.school_id = sc.school_id
where ds.is_active = true