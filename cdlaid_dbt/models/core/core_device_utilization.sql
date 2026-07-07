with device_usage as (

    select *
    from mart.fact_device_usage
    -- from {{ ref('stg_device_usage') }}

)

select
    school_id,
    date_key,

    count(distinct device_id) as active_devices,

    avg(total_usage_minutes) as avg_usage_minutes,

    sum(session_count) as total_sessions,

    sum(total_usage_minutes) as total_usage_minutes

from device_usage
group by school_id, date_key