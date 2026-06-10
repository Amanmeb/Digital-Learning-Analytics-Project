-- Staging model for AI interaction events
-- Reads from raw xAPI statements and extracts AI usage data

with raw_ai as (
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
    where verb->>'id' = 'https://camara.org/xapi/verbs/ai-queried'
)

select
    statement_id,
    school_id,
    actor->'account'->>'name'                                       as student_id,
    object->>'id'                                                   as ai_service_id,
    result->>'duration'                                             as duration_iso,
    context->'extensions'->'https://camara.org/xapi/context'->>'subject_id'  as subject_id,
    context->'extensions'->'https://camara.org/xapi/context'->>'query_type'  as query_type,
    context->'extensions'->'https://camara.org/xapi/context'->>'platform_id' as platform_id,
    context->'extensions'->'https://camara.org/xapi/context'->>'is_offline'  as is_offline_str,
    timestamp::timestamptz                                          as event_timestamp,
    event_fingerprint
from raw_ai
