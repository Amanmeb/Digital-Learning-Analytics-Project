-- Mart model for per-device health and bandwidth
-- Supporting dataset for the Device and Infrastructure dashboard,
-- alongside mart_device_infrastructure (sync health)
select
    device_id,
    school_id,
    device_name,
    device_type,
    os,
    assigned_location,
    health_score,
    bandwidth_used_mb_daily,
    last_seen_at,
    health_status,
    current_timestamp                           as refreshed_at
from {{ ref("core_device_health") }}