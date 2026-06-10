-- Staging model for session events
-- Reads from raw xAPI statements and extracts session data
-- Filters for session-started and session-ended verbs only
with raw_sessions as (
    select
        statement_id,
        school_id,
        server_id,
        actor,
        verb,
        object,
        result,
        context,
        timestamp,
        event_fingerprint
    from raw.xapi_statements
    where verb->>'id' in (
        'https://camara.org/xapi/verbs/session-started',
        'https://camara.org/xapi/verbs/session-ended'
    )
)
select
    statement_id,
    school_id,
    server_id,
    actor->>'objectType'                                        as actor_type,
    actor->'account'->>'name'                                   as student_id,
    verb->>'id'                                                 as verb_id,
    object->>'id'                                               as session_activity_id,
    result->>'duration'                                         as duration_iso,
    context->'extensions'->'https://camara.org/xapi/context'->>'device_id'   as device_id,
    context->'extensions'->'https://camara.org/xapi/context'->>'platform_id' as platform_id,
    context->'extensions'->'https://camara.org/xapi/context'->>'is_offline'  as is_offline_str,
    context->'extensions'->'https://camara.org/xapi/context'->>'tracking_depth' as tracking_depth,
    timestamp::timestamptz                                      as event_timestamp,
    event_fingerprint
from raw_sessions