-- Mart model for Student Engagement dashboard
-- Pre-aggregates per-student engagement metrics

with engagement as (
    select
        student_id,
        school_id,
        sum(session_count)                      as total_sessions,
        count(distinct session_date)            as active_days,
        round(avg(avg_session_duration_minutes)::numeric, 2) as avg_session_duration_minutes,
        round(sum(total_session_minutes)::numeric, 2) as total_learning_minutes,
        bool_or(is_offline)                     as any_offline
    from {{ ref("core_student_engagement") }}
    group by student_id, school_id
),

consistency as (
    select
        student_id,
        school_id,
        consistency_score,
        active_days,
        first_active_date,
        last_active_date
    from {{ ref("core_learning_consistency") }}
),

first_week as (
    select
        student_id,
        school_id,
        activated_in_first_week,
        days_to_first_session
    from {{ ref("core_first_week_activation") }}
)

select
    e.student_id,
    e.school_id,
    e.total_sessions,
    e.active_days,
    e.avg_session_duration_minutes,
    e.total_learning_minutes,
    e.any_offline,
    c.consistency_score,
    c.first_active_date,
    c.last_active_date,
    f.activated_in_first_week,
    f.days_to_first_session,
    current_timestamp                           as refreshed_at
from engagement e
left join consistency c
    on e.student_id = c.student_id
    and e.school_id = c.school_id
left join first_week f
    on e.student_id = f.student_id
    and e.school_id = f.school_id
