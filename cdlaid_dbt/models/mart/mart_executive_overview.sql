-- Mart model for Executive Overview dashboard
-- Pre-aggregates national and regional KPIs
-- Refreshed nightly by cron job

with school_summary as (
    select
        s.school_id,
        r.region_id,
        r.region_name,
        s.school_name,
        s.school_type,
        sum(ss.active_students)                 as total_active_students,
        sum(ss.total_sessions)                  as total_sessions,
        sum(ss.total_learning_minutes)          as total_learning_minutes,
        sum(ss.offline_sessions)                as offline_sessions,
        sum(ss.students_used_ai)                as students_used_ai
    from {{ ref("core_school_summary") }} ss
    join mart.dim_school s on ss.school_id = s.school_id
    join mart.dim_region r on s.region_id = r.region_id
    group by s.school_id, r.region_id, r.region_name, s.school_name, s.school_type
),

national_totals as (
    select
        count(distinct school_id)               as active_schools,
        sum(total_active_students)              as total_active_students,
        sum(total_sessions)                     as total_sessions,
        round(sum(total_learning_minutes) / 60.0, 2) as total_learning_hours,
        sum(offline_sessions)                   as offline_sessions,
        case
            when sum(total_sessions) > 0
            then round(sum(offline_sessions)::numeric / sum(total_sessions) * 100, 2)
            else 0
        end                                     as offline_usage_pct,
        case
            when sum(total_sessions) > 0
            then round(sum(students_used_ai)::numeric / sum(total_active_students) * 100, 2)
            else 0
        end                                     as ai_adoption_rate_pct
    from school_summary
)

select
    active_schools,
    total_active_students,
    total_sessions,
    total_learning_hours,
    offline_usage_pct,
    ai_adoption_rate_pct,
    current_timestamp                           as refreshed_at
from national_totals
