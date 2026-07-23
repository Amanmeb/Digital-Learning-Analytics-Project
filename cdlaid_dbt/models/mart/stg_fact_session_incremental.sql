-- Mart model that populates the real mart.fact_session table
-- incrementally. Uses the proven two-table pattern already used for
-- fact_resource_usage: this is a dbt-owned intermediate table, and a
-- post_hook INSERTs new rows into the real constrained fact_session
-- table with ON CONFLICT DO NOTHING. This avoids dbt silently
-- dropping and recreating a manually-constrained table -- see
-- stg_resource_usage_incremental.sql for the original discovery of
-- this failure mode.

{{ config(
    materialized="incremental",
    unique_key="session_id",
    post_hook=["insert into mart.fact_session select * from {{ this }} where session_id not in (select session_id from mart.fact_session) on conflict (session_id) do nothing"]
) }}

select
    session_uuid                as session_id,
    student_id,
    school_id,
    device_id,
    platform_id,
    null::integer                as date_key,
    null::varchar(20)            as project_id,
    session_duration_minutes,
    is_offline,
    session_start,
    session_end,
    event_fingerprint,
    now()                        as created_at
from {{ ref("core_sessions") }}
{% if is_incremental() %}
where session_uuid not in (select session_id from {{ this }})
{% endif %}