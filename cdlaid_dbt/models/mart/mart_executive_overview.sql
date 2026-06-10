-- Mart model for Executive Overview dashboard
-- Produces daily rows for trend charts plus national KPI totals
-- One row per day per school for trend lines
-- Aggregate in Superset for national totals

with school_summary as (
    select
        s.school_id,
        s.school_name,
        s.school_type,
        r.region_id,
        r.region_name,
        ss.summary_date,
        ss.active_students,
        ss.total_sessions,
        ss.total_learning_minutes,
        ss.offline_sessions,
        ss.students_used_ai
    from {{ ref("core_school_summary") }} ss
    join mart.dim_school s on ss.school_id = s.school_id
    join mart.dim_region r on s.region_id = r.region_id
),

registered as (
    select
        school_id,
        count(*) as total_registered_students
    from mart.dim_student
    where is_active = true
    group by school_id
)

select
    ss.summary_date,
    ss.school_id,
    ss.school_name,
    ss.school_type,
    ss.region_id,
    ss.region_name,
    ss.active_students,
    ss.total_sessions,
    round(ss.total_learning_minutes / 60.0, 2)          as total_learning_hours,
    ss.offline_sessions,
    ss.students_used_ai,
    case
        when ss.total_sessions > 0
        then round(ss.offline_sessions::numeric / ss.total_sessions * 100, 2)
        else 0
    end                                                 as offline_usage_pct,
    case
        when ss.active_students > 0
        then round(ss.students_used_ai::numeric / ss.active_students * 100, 2)
        else 0
    end                                                 as ai_adoption_rate_pct,
    coalesce(r.total_registered_students, 0)            as total_registered_students,
    case
        when coalesce(r.total_registered_students, 0) > 0
        then round(ss.active_students::numeric / r.total_registered_students * 100, 2)
        else 0
    end                                                 as active_rate_pct,
    current_timestamp                                   as refreshed_at
from school_summary ss
left join registered r on ss.school_id = r.school_id