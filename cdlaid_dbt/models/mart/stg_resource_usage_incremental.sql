-- Mart model for device tracking resource usage
-- Populates the existing fact_resource_usage table incrementally
-- Only closed/ended events carry duration -- opened/started events are
-- logged in raw for audit but not needed here since duration is
-- already known once the closing event arrives
--
-- Explicitly joins against stg_fact_session_incremental (not just a
-- raw SQL post_hook dependency) for two reasons: it creates a real
-- dbt DAG dependency so this model always runs after session data
-- exists, and it filters out any resource event whose session_id
-- was never captured -- both needed after discovering that
-- fact_resource_usage's session_id foreign key requires a real,
-- already-populated fact_session row.
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
),

valid_sessions as (
    -- Referencing stg_fact_session_incremental via ref() creates a
    -- real dbt dependency, guaranteeing session data exists before
    -- this model runs, and lets us filter to only real sessions
    select session_id
    from {{ ref("stg_fact_session_incremental") }}
)

select
    'RES-' || ce.event_fingerprint                              as resource_usage_id,
    ce.session_id,
    ce.resource_id,
    case
        when ce.verb_id = 'https://camara.org/xapi/verbs/app-closed'  then 'app'
        when ce.verb_id = 'https://camara.org/xapi/verbs/site-left'   then 'site'
        when ce.verb_id = 'https://camara.org/xapi/verbs/book-closed' then 'book'
        when ce.verb_id = 'https://camara.org/xapi/verbs/idle-ended'  then 'idle'
    end                                                          as activity_type,
    null::integer                                                as date_key,
    ce.event_timestamp - (extract(epoch from ce.duration_iso::interval) * interval '1 second') as start_time,
    ce.event_timestamp                                           as end_time,
    extract(epoch from ce.duration_iso::interval)::integer       as duration_seconds,
    null::varchar(20)                                            as ai_service_id,
    null::integer                                                as ai_query_count,
    ce.event_fingerprint,
    now()                                                        as created_at
from closed_events ce
inner join valid_sessions vs on ce.session_id = vs.session_id
{% if is_incremental() %}
where ce.event_fingerprint not in (select event_fingerprint from {{ this }})
{% endif %}