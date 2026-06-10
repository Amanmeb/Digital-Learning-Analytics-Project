-- Core model for content performance metrics
-- Calculates completion rates and time spent per content item
-- Used by mart_content_performance

with content as (
    select
        content_id,
        content_name,
        student_id,
        school_id,
        platform_id,
        completion_status,
        case
            when duration_iso is not null
            then extract(epoch from duration_iso::interval) / 60
            else null
        end                                             as duration_minutes,
        event_timestamp
    from {{ ref("stg_content_usage") }}
),

content_summary as (
    select
        content_id,
        content_name,
        school_id,
        platform_id,
        count(*)                                        as total_accesses,
        count(distinct student_id)                      as unique_students,
        count(*) filter (where completion_status = 'Completed') as completed_count,
        avg(duration_minutes)                           as avg_time_spent_minutes,
        sum(duration_minutes)                           as total_time_spent_minutes,
        min(event_timestamp)                            as first_accessed_at,
        max(event_timestamp)                            as last_accessed_at
    from content
    group by content_id, content_name, school_id, platform_id
)

select
    content_id,
    content_name,
    school_id,
    platform_id,
    total_accesses,
    unique_students,
    completed_count,
    case
        when total_accesses > 0
        then round((completed_count::numeric / total_accesses) * 100, 2)
        else 0
    end                                                 as completion_rate_pct,
    round(avg_time_spent_minutes::numeric, 2)           as avg_time_spent_minutes,
    round(total_time_spent_minutes::numeric, 2)         as total_time_spent_minutes,
    first_accessed_at,
    last_accessed_at
from content_summary
