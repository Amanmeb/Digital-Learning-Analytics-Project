-- Core model that pairs session-started and session-ended events into
-- one row per real session. Extracts the session_id from the object id
-- (format: .../session/<uuid>), matching the pattern emitter.py and
-- device_tracker.py both already use for real session events.
-- This feeds mart.stg_fact_session_incremental, which populates the
-- real mart.fact_session table.

with session_events as (
    select
        statement_id,
        school_id,
        student_id,
        verb_id,
        device_id,
        platform_id,
        is_offline_str,
        duration_iso,
        event_timestamp,
        event_fingerprint,
        -- extracts the uuid after the last slash in the session activity id
        split_part(session_activity_id, '/', -1) as session_uuid
    from {{ ref("stg_sessions") }}
    where session_activity_id like '%/session/%'
),

paired as (
    select
        session_uuid,
        student_id,
        school_id,
        min(event_timestamp) filter (where verb_id = 'https://camara.org/xapi/verbs/session-started') as session_start,
        max(event_timestamp) filter (where verb_id = 'https://camara.org/xapi/verbs/session-ended')   as session_end,
        max(duration_iso)    filter (where verb_id = 'https://camara.org/xapi/verbs/session-ended')   as duration_iso,
        max(device_id)       filter (where device_id is not null)                                      as device_id,
        max(platform_id)     filter (where platform_id is not null)                                    as platform_id,
        bool_or(is_offline_str::boolean)                                                                as is_offline,
        max(event_fingerprint) filter (where verb_id = 'https://camara.org/xapi/verbs/session-ended')  as end_fingerprint,
        max(event_fingerprint) filter (where verb_id = 'https://camara.org/xapi/verbs/session-started') as start_fingerprint
    from session_events
    group by session_uuid, student_id, school_id
)

select
    session_uuid,
    student_id,
    school_id,
    device_id,
    platform_id,
    is_offline,
    session_start,
    session_end,
    case
        when duration_iso is not null
        then round(extract(epoch from duration_iso::interval) / 60)::integer
        when session_start is not null and session_end is not null
        then round(extract(epoch from (session_end - session_start)) / 60)::integer
        else 0
    end as session_duration_minutes,
    coalesce(end_fingerprint, start_fingerprint) as event_fingerprint
from paired
where session_start is not null