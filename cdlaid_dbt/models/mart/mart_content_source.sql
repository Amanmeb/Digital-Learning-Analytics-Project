-- Mart model for Content Source Analytics dashboard
-- Pre-aggregates content usage by provider

with content_with_provider as (
    select
        cp.content_id,
        cp.school_id,
        cp.total_accesses,
        cp.unique_students,
        cp.completed_count,
        cp.completion_rate_pct,
        cp.avg_time_spent_minutes,
        dc.provider_id
    from {{ ref("core_content_performance") }} cp
    left join mart.dim_content dc on cp.content_id = dc.content_id
)

select
    c.provider_id,
    p.provider_name,
    p.provider_type,
    c.school_id,
    sum(c.total_accesses)                       as total_accesses,
    count(distinct c.unique_students)           as unique_students,
    round(avg(c.completion_rate_pct)::numeric, 2) as avg_completion_rate_pct,
    round(avg(c.avg_time_spent_minutes)::numeric, 2) as avg_time_spent_minutes,
    case
        when avg(c.completion_rate_pct) < {{ var("completion_flag") }}
        or sum(c.total_accesses) < 100
        then 'RISK'
        else 'OK'
    end                                         as risk_flag,
    current_timestamp                           as refreshed_at
from content_with_provider c
left join mart.dim_content_provider p on c.provider_id = p.provider_id
group by c.provider_id, p.provider_name, p.provider_type, c.school_id
