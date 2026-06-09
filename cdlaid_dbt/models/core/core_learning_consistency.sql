-- Core model for learning consistency metrics
-- Calculates streak distribution and active day ratios
-- Used by mart_student_engagement

with daily_activity as (
    select
        student_id,
        school_id,
        session_date,
        sum(session_count)                      as daily_sessions
    from {{ ref("core_student_engagement") }}
    group by student_id, school_id, session_date
),

date_range as (
    select
        student_id,
        school_id,
        min(session_date)                       as first_active_date,
        max(session_date)                       as last_active_date,
        count(distinct session_date)            as active_days,
        max(session_date) - min(session_date) + 1 as total_days_span
    from daily_activity
    group by student_id, school_id
)

select
    student_id,
    school_id,
    first_active_date,
    last_active_date,
    active_days,
    total_days_span,
    case
        when total_days_span > 0
        then round(active_days::numeric / total_days_span, 4)
        else 0
    end                                         as consistency_score
from date_range
