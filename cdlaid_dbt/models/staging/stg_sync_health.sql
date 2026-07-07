{{ config(materialized='view') }}

select
    sync_health_id,
    device_id,
    school_id,
    date_key,
    status,
    records_synced,
    sync_duration_secs
from mart.fact_sync_health