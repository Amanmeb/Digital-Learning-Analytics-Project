-- Core model for student engagement metrics
-- Calculates session-level engagement metrics per student
-- Used by mart_student_engagement and mart_executive_overview

with sessions as (
    select
        student_id,
        school_id,
        platform_id,
        device_id,
        is_offline_str::boolean                         as is_offline,
        event_timestamp::date                           as session_date,
        case
            when verb_id = 'https://camara.org/xapi/verbs/session-started'
            then statement_id
        end                                             as session_start_id,
        case
            when duration_iso is not null
            then extract(epoch from duration_iso::interval) / 60
            else null
        end                                             as duration_minutes
    from {{ ref("stg_sessions") }}
    where student_id not like '%%-TCH-%%'
),

session_summary as (
    select
        student_id,
        school_id,
        platform_id,
        session_date,
        count(distinct session_start_id)                as session_count,
        avg(duration_minutes)                           as avg_duration_minutes,
        sum(duration_minutes)                           as total_duration_minutes,
        bool_or(is_offline)                             as any_offline
    from sessions
    group by student_id, school_id, platform_id, session_date
)

select
    student_id,
    school_id,
    platform_id,
    session_date,
    session_count,
    round(avg_duration_minutes::numeric, 2)             as avg_session_duration_minutes,
    round(total_duration_minutes::numeric, 2)           as total_session_minutes,
    any_offline                                         as is_offline
from session_summary
