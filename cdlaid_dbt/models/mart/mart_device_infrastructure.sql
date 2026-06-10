-- Mart model for Device and Infrastructure dashboard
-- Pre-aggregates sync health and device usage metrics

select
    school_id,
    sync_date,
    total_syncs,
    successful_syncs,
    sync_health_pct,
    sync_status,
    current_timestamp                           as refreshed_at
from {{ ref("core_platform_availability") }}
