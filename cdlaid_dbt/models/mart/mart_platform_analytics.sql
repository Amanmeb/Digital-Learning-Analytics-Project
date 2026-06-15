-- Mart model for Platform Analytics dashboard
-- Pre-aggregates usage metrics per platform
-- Includes completion rate, AI queries, and risk flag from settings
-- Note: platform_availability_rate_pct defaults to 100 until FactPortalJob data flows

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
),

platform_content as (
    select
        school_id,
        platform_id,
        count(*)                                as total_content_accesses,
        sum(completed_count)                    as total_completed,
        case
            when count(*) > 0
            then round(sum(completed_count)::numeric / count(*) * 100, 2)
            else 0
        end                                     as completion_rate_pct
    from {{ ref("core_content_performance") }}
    group by school_id, platform_id
),

platform_ai as (
    select
        school_id,
        platform_id,
        count(*)                                as total_ai_queries,
        count(distinct student_id)              as students_used_ai
    from {{ ref("stg_ai_usage") }}
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
    coalesce(c.completion_rate_pct, 0)          as completion_rate_pct,
    coalesce(a.total_ai_queries, 0)             as total_ai_queries,
    coalesce(a.students_used_ai, 0)             as students_used_ai,
    100                                         as availability_rate_pct,
    case
        when coalesce(c.completion_rate_pct, 0) < {{ get_setting("platform_risk_flag") | float }}
        then 'RISK'
        else 'OK'
    end                                         as risk_flag,
    current_timestamp                           as refreshed_at
from platform_usage u
join mart.dim_platform p on u.platform_id = p.platform_id
left join platform_content c
    on u.school_id = c.school_id
    and u.platform_id = c.platform_id
left join platform_ai a
    on u.school_id = a.school_id
    and u.platform_id = a.platform_id