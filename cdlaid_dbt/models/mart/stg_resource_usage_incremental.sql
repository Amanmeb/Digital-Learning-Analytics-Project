-- Mart model for device tracking resource usage
-- Populates the existing fact_resource_usage table incrementally
-- Only closed/ended events carry duration -- opened/started events are
-- logged in raw for audit but not needed here since duration is
-- already known once the closing event arrives
{{ config(
    materialized="incremental",
    unique_key="resource_usage_id",
    post_hook=["insert into mart.dim_resource_catalog (resource_id, resource_name, resource_type, discovery_method, is_reviewed, is_active) select distinct resource_id, resource_id, case when resource_id like 'idle-%' then 'idle' when resource_id like '%app%' then 'app' when resource_id like 'http%' then 'site' else 'unknown' end, 'auto_discovery', false, true from {{ this }} where resource_id is not null and resource_id not in (select resource_id from mart.dim_resource_catalog) on conflict (resource_id) do nothing", "insert into mart.fact_resource_usage select * from {{ this }} where event_fingerprint not in (select event_fingerprint from mart.fact_resource_usage) on conflict (resource_usage_id) do nothing"]
) }}
with closed_events as (
    select
        statement_id,
        school_id,
        student_id,
        verb_id,
        resource_id,
        session_id,
        duration_iso,
        event_timestamp,
        event_fingerprint
    from {{ ref("stg_resource_events") }}
    where verb_id in (
        'https://camara.org/xapi/verbs/app-closed',
        'https://camara.org/xapi/verbs/site-left',
        'https://camara.org/xapi/verbs/book-closed',
        'https://camara.org/xapi/verbs/idle-ended'
    )
)
select
    'RES-' || event_fingerprint                                 as resource_usage_id,
    session_id,
    resource_id,
    case
        when verb_id = 'https://camara.org/xapi/verbs/app-closed'  then 'app'
        when verb_id = 'https://camara.org/xapi/verbs/site-left'   then 'site'
        when verb_id = 'https://camara.org/xapi/verbs/book-closed' then 'book'
        when verb_id = 'https://camara.org/xapi/verbs/idle-ended'  then 'idle'
    end                                                          as activity_type,
    null::integer                                                as date_key,
    event_timestamp - (extract(epoch from duration_iso::interval) * interval '1 second') as start_time,
    event_timestamp                                              as end_time,
    extract(epoch from duration_iso::interval)::integer          as duration_seconds,
    null::varchar(20)                                            as ai_service_id,
    null::integer                                                as ai_query_count,
    event_fingerprint,
    now()                                                        as created_at
from closed_events
{% if is_incremental() %}
where event_fingerprint not in (select event_fingerprint from {{ this }})
{% endif %}