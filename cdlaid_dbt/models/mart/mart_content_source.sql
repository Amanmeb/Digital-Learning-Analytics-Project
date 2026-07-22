-- Mart model for Content Source Analytics dashboard
-- Pre-aggregates content usage by provider
-- Includes language breakdown and risk flag from settings

with content_with_provider as (
    select
        cp.content_id,
        cp.school_id,
        cp.total_accesses,
        cp.unique_students,
        cp.completed_count,
        cp.completion_rate_pct,
        cp.avg_time_spent_minutes,
        dc.provider_id,
        dc.language_id
    from {{ ref("core_content_performance") }} cp
    left join mart.dim_content dc on cp.content_id = dc.content_id
),

provider_summary as (
    select
        c.provider_id,
        c.school_id,
        c.language_id,
        sum(c.total_accesses)                       as total_accesses,
        sum(c.unique_students)                      as unique_students,
        sum(c.completed_count)                      as total_completed,
        round(avg(c.completion_rate_pct)::numeric, 2) as avg_completion_rate_pct,
        round(avg(c.avg_time_spent_minutes)::numeric, 2) as avg_time_spent_minutes
    from content_with_provider c
    group by c.provider_id, c.school_id, c.language_id
)

select
    ps.provider_id,
    p.provider_name,
    p.provider_type,
    ps.school_id,
    l.language_name,
    ps.total_accesses,
    ps.unique_students,
    ps.total_completed,
    ps.avg_completion_rate_pct,
    ps.avg_time_spent_minutes,
    case
        when ps.avg_completion_rate_pct < {{ get_setting("provider_risk_flag") | float }}
        or ps.total_accesses < 100
        then 'RISK'
        else 'OK'
    end                                         as risk_flag,
    current_timestamp                           as refreshed_at
from provider_summary ps
left join mart.dim_content_provider p on ps.provider_id = p.provider_id
left join mart.dim_language l on ps.language_id = l.language_id