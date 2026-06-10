-- Core model for teacher engagement metrics
-- Tracks teacher platform usage and session patterns
-- Used by mart_school_performance

with teacher_sessions as (
    select
        teacher_id,
        school_id,
        platform_id,
        device_id,
        event_timestamp::date                   as session_date,
        case
            when duration_iso is not null
            then extract(epoch from duration_iso::interval) / 60
            else null
        end                                     as duration_minutes
    from {{ ref("stg_teacher_sessions") }}
)

select
    teacher_id,
    school_id,
    session_date,
    count(*)                                    as session_count,
    count(distinct platform_id)                 as platforms_used,
    count(distinct device_id)                   as devices_used,
    round(avg(duration_minutes)::numeric, 2)    as avg_session_minutes,
    round(sum(duration_minutes)::numeric, 2)    as total_session_minutes
from teacher_sessions
group by teacher_id, school_id, session_date
