-- Mart model for Content Performance dashboard
-- Pre-aggregates content usage and completion metrics
-- Includes staleness flag and problematic content flag
-- Thresholds read from ops.settings

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
        when completion_rate_pct < {{ get_setting("completion_flag") | float }}
        then 'FLAGGED'
        else 'OK'
    end                                         as completion_flag,
    case
        when last_accessed_at is not null
        and current_date - last_accessed_at::date > {{ get_setting("content_stale_days") | int }}
        then true
        else false
    end                                         as is_stale,
    case
        when last_accessed_at is not null
        then current_date - last_accessed_at::date
        else null
    end                                         as days_since_last_access,
    current_timestamp                           as refreshed_at
from {{ ref("core_content_performance") }}