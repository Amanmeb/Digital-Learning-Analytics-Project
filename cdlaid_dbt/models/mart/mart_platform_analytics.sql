-- Mart model for Platform Analytics dashboard
-- Pre-aggregates usage metrics per platform

with platform_usage as (
    select
        school_id,
        platform_id,
        count(distinct student_id)              as unique_students,
        sum(session_count)                      as total_sessions,
        round(avg(avg_session_duration_minutes)::numeric, 2) as avg_session_minutes,
        round(sum(total_session_minutes)::numeric, 2) as total_minutes,
        count(*) filter (where is_offline)      as offline_sessions
    from {{ ref("core_student_engagement") }}
    group by school_id, platform_id
)

select
    u.school_id,
    u.platform_id,
    p.platform_name,
    p.platform_type,
    p.tracking_depth,
    u.unique_students,
    u.total_sessions,
    u.avg_session_minutes,
    u.total_minutes,
    u.offline_sessions,
    case
        when u.total_sessions > 0
        then round(u.offline_sessions::numeric / u.total_sessions * 100, 2)
        else 0
    end                                         as offline_pct,
    current_timestamp                           as refreshed_at
from platform_usage u
join mart.dim_platform p on u.platform_id = p.platform_id
