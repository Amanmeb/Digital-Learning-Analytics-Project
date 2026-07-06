-- Staging model for device tracking resource events
-- Reads from raw xAPI statements and extracts app, site, book, and idle events
with raw_resource_events as (
    select
        statement_id,
        school_id,
        actor,
        verb,
        object,
        result,
        context,
        timestamp,
        event_fingerprint
    from raw.xapi_statements
    where verb->>'id' in (
        'https://camara.org/xapi/verbs/app-opened',
        'https://camara.org/xapi/verbs/app-closed',
        'https://camara.org/xapi/verbs/site-visited',
        'https://camara.org/xapi/verbs/site-left',
        'https://camara.org/xapi/verbs/book-opened',
        'https://camara.org/xapi/verbs/book-closed',
        'https://camara.org/xapi/verbs/idle-started',
        'https://camara.org/xapi/verbs/idle-ended'
    )
)
select
    statement_id,
    school_id,
    actor->'account'->>'name'                                   as student_id,
    verb->>'id'                                                 as verb_id,
    case
        when verb->>'id' in ('https://camara.org/xapi/verbs/idle-started', 'https://camara.org/xapi/verbs/idle-ended')
        then replace(object->>'id', 'https://camara.org/xapi/activities/session/', 'idle-')
        else replace(object->>'id', 'https://camara.org/xapi/activities/resource/', '')
    end                                                          as resource_id,
    result->>'duration'                                         as duration_iso,
    context->'extensions'->'https://camara.org/xapi/context'->>'session_id'  as session_id,
    context->'extensions'->'https://camara.org/xapi/context'->>'device_id'   as device_id,
    context->'extensions'->'https://camara.org/xapi/context'->>'platform_id' as platform_id,
    context->'extensions'->'https://camara.org/xapi/context'->>'is_offline'  as is_offline_str,
    timestamp::timestamptz                                      as event_timestamp,
    event_fingerprint
from raw_resource_events