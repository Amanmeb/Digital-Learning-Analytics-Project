-- Staging model for teacher session events
-- Same structure as student sessions but for teacher actors

with raw_teacher_sessions as (
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
    and actor->'account'->>'name' like '%-TCH-%'
)

select
    statement_id,
    school_id,
    server_id,
    actor->'account'->>'name'                                       as teacher_id,
    verb->>'id'                                                     as verb_id,
    object->>'id'                                                   as session_activity_id,
    result->>'duration'                                             as duration_iso,
    context->'extensions'->'https://camara.org/xapi/context'->>'device_id'   as device_id,
    context->'extensions'->'https://camara.org/xapi/context'->>'platform_id' as platform_id,
    context->'extensions'->'https://camara.org/xapi/context'->>'is_offline'  as is_offline_str,
    timestamp::timestamptz                                          as event_timestamp,
    event_fingerprint
from raw_teacher_sessions
