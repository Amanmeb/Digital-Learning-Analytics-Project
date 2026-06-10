-- Mart model for School Performance dashboard
-- Calculates school-level performance index and risk flags

with school_metrics as (
    select
        s.school_id,
        s.school_name,
        s.region_id,
        s.school_type,
        s.total_students,
        sum(ss.active_students)                 as active_students,
        sum(ss.total_sessions)                  as total_sessions,
        sum(ss.total_learning_minutes)          as total_learning_minutes,
        max(ss.summary_date)                    as last_active_date
    from {{ ref("core_school_summary") }} ss
    join mart.dim_school s on ss.school_id = s.school_id
    group by s.school_id, s.school_name, s.region_id, s.school_type, s.total_students
),

school_scores as (
    select
        school_id,
        school_name,
        region_id,
        school_type,
        total_students,
        active_students,
        total_sessions,
        round(total_learning_minutes / 60.0, 2)     as total_learning_hours,
        last_active_date,
        case
            when total_students > 0
            then round(active_students::numeric / total_students * 100, 2)
            else 0
        end                                         as registration_coverage_pct,
        case
            when total_students > 0
            then round(
                (active_students::numeric / total_students * 0.6) +
                (least(total_sessions::numeric / greatest(active_students, 1) / 10, 1) * 0.4),
                4
            )
            else 0
        end                                         as performance_index
    from school_metrics
)

select
    school_id,
    school_name,
    region_id,
    school_type,
    total_students,
    active_students,
    total_sessions,
    total_learning_hours,
    registration_coverage_pct,
    performance_index,
    last_active_date,
    case
        when registration_coverage_pct < {{ var("school_coverage_flag") }}
        or performance_index < {{ var("school_performance_flag") }}
        then 'RISK'
        else 'OK'
    end                                             as risk_flag,
    current_timestamp                               as refreshed_at
from school_scores
