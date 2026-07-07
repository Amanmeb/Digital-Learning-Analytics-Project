{{ config(materialized='view') }}

select
    device_usage_id,
    device_id,
    school_id,
    date_key,
    total_usage_minutes,
    session_count
from mart.fact_device_usage