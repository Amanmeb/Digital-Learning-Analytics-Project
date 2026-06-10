-- Mart model for Content Performance dashboard
-- Pre-aggregates content usage and completion metrics

select
    content_id,
    content_name,
    school_id,
    platform_id,
    total_accesses,
    unique_students,
    completed_count,
    completion_rate_pct,
    avg_time_spent_minutes,
    total_time_spent_minutes,
    first_accessed_at,
    last_accessed_at,
    case
        when completion_rate_pct < {{ var("completion_flag") }}
        then 'FLAGGED'
        else 'OK'
    end                                         as completion_flag,
    current_timestamp                           as refreshed_at
from {{ ref("core_content_performance") }}
