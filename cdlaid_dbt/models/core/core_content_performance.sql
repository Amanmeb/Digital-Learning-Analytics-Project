-- Core model for content performance metrics
-- Calculates completion rates and time spent per content item
-- Used by mart_content_performance

with content as (

    select
        s.content_id,
        s.content_name,
        s.student_id,
        s.school_id,
        s.platform_id,
        s.completion_status,

        case
            when s.duration_iso is not null
            then extract(epoch from s.duration_iso::interval) / 60
            else null
        end as duration_minutes,

        s.event_timestamp,
        d.date_key

    from {{ ref("stg_content_usage") }} s

    left join mart.dim_date d
        on s.event_timestamp::date = d.full_date

),

content_summary as (

    select
        content_id,
        content_name,
        school_id,
        platform_id,
        date_key,

        count(*) as total_accesses,
        count(distinct student_id) as unique_students,
        count(*) filter (
            where completion_status = 'Completed'
        ) as completed_count,

        avg(duration_minutes) as avg_time_spent_minutes,
        sum(duration_minutes) as total_time_spent_minutes,

        min(event_timestamp) as first_accessed_at,
        max(event_timestamp) as last_accessed_at

    from content

    group by
        content_id,
        content_name,
        school_id,
        platform_id,
        date_key

)

select
    content_id,
    content_name,
    school_id,
    platform_id,
    date_key,
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
