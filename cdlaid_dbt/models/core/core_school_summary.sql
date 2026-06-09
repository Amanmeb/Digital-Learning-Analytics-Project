-- Core model for school-level daily summary metrics
-- Aggregates student and session counts per school per day
-- Used by mart_school_performance and mart_executive_overview

with sessions as (
    select
        school_id,
        student_id,
        session_date,
        total_session_minutes,
        is_offline
    from {{ ref("core_student_engagement") }}
),

ai_usage as (
    select
        school_id,
        student_id,
        event_timestamp::date   as usage_date
    from {{ ref("stg_ai_usage") }}
),

content_usage as (
    select
        school_id,
        student_id,
        event_timestamp::date   as usage_date
    from {{ ref("stg_content_usage") }}
)

select
    s.school_id,
    s.session_date                                      as summary_date,
    count(distinct s.student_id)                        as active_students,
    count(*)                                            as total_sessions,
    round(sum(s.total_session_minutes)::numeric, 2)     as total_learning_minutes,
    count(*) filter (where s.is_offline)                as offline_sessions,
    count(distinct a.student_id)                        as students_used_ai,
    count(distinct c.student_id)                        as students_accessed_content
from sessions s
left join ai_usage a
    on s.school_id = a.school_id
    and s.student_id = a.student_id
    and s.session_date = a.usage_date
left join content_usage c
    on s.school_id = c.school_id
    and s.student_id = c.student_id
    and s.session_date = c.usage_date
group by s.school_id, s.session_date
