-- Staging model for content usage events
-- Reads from raw xAPI statements and extracts content access and completion data

with raw_content as (
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
        'http://adlnet.gov/expapi/verbs/experienced',
        'http://adlnet.gov/expapi/verbs/completed'
    )
)

select
    statement_id,
    school_id,
    actor->'account'->>'name'                                   as student_id,
    verb->>'id'                                                 as verb_id,
    object->>'id'                                               as content_id,
    object->'definition'->'name'->>'en-US'                      as content_name,
    result->>'duration'                                         as duration_iso,
    result->>'completion'                                       as completion_str,
    result->'extensions'->>'https://camara.org/xapi/activities/result/completion-status' as completion_status,
    context->'extensions'->'https://camara.org/xapi/context'->>'platform_id' as platform_id,
    context->'extensions'->'https://camara.org/xapi/context'->>'device_id'   as device_id,
    context->'extensions'->'https://camara.org/xapi/context'->>'is_offline'  as is_offline_str,
    timestamp::timestamptz                                      as event_timestamp,
    event_fingerprint
from raw_content
