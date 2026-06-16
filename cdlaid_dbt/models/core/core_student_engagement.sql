-- Core model for student engagement metrics
-- Calculates session-level engagement metrics per student
-- Uses session-ended duration_iso when available
-- Falls back to last heartbeat timestamp when duration_iso is null
-- This handles cases where connection dropped before session-ended was emitted

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
            when verb_id = 'https://camara.org/xapi/verbs/session-started'
            then event_timestamp
        end                                             as session_start_time,
        case
            when duration_iso is not null
            then extract(epoch from duration_iso::interval) / 60
            else null
        end                                             as duration_minutes,
        session_activity_id
    from {{ ref("stg_sessions") }}
    where student_id not like '%%-TCH-%%'
),

heartbeats as (
    -- Gets the last heartbeat per session to estimate duration
    -- when session-ended was never emitted
    select
        context->'extensions'->'https://camara.org/xapi/context'->>'school_id'  as school_id,
        actor->'account'->>'name'                                                as student_id,
        object->>'id'                                                            as session_activity_id,
        max(timestamp::timestamptz)                                              as last_heartbeat_time
    from raw.xapi_statements
    where verb->>'id' = 'https://camara.org/xapi/verbs/session-heartbeat'
    and actor->'account'->>'name' not like '%-TCH-%'
    group by
        context->'extensions'->'https://camara.org/xapi/context'->>'school_id',
        actor->'account'->>'name',
        object->>'id'
),

session_with_heartbeat as (
    -- Joins sessions with heartbeat data
    -- Uses duration_minutes from session-ended when available
    -- Falls back to minutes between session-started and last heartbeat
    select
        s.student_id,
        s.school_id,
        s.platform_id,
        s.session_date,
        s.session_start_id,
        s.is_offline,
        case
            when s.duration_minutes is not null
            then s.duration_minutes
            when s.session_start_time is not null
                and h.last_heartbeat_time is not null
            then extract(
                epoch from (
                    h.last_heartbeat_time - s.session_start_time::timestamptz
                )
            ) / 60
            else null
        end                                             as duration_minutes
    from sessions s
    left join heartbeats h
        on  s.school_id           = h.school_id
        and s.student_id          = h.student_id
        and s.session_activity_id = h.session_activity_id
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
    from session_with_heartbeat
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