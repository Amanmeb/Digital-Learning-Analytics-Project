-- Core model for device health and bandwidth
-- Surfaces per-device health score, bandwidth, and last seen
-- Source data populated by tracking agents via the device registration
-- and heartbeat path -- not yet built (ST-13/ST-14), so this model is
-- correct now and will simply show real data once those agents exist
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
    case
        when health_score is not null
            and health_score < ({{ get_setting("device_health_score_min", "70") }})::numeric
        then 'flagged'
        else 'ok'
    end                                         as health_status
from mart.dim_device