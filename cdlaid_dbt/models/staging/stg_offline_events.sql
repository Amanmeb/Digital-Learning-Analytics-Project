select
    id::text as statement_id,
    fingerprint,
    school_id,
    device_id,
    statement,
    received_at
from mart.stg_offline_events
where processed = false


