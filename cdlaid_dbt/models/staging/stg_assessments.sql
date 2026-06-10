-- Staging model for assessment attempt events
-- Reads from raw xAPI statements and extracts assessment data

with raw_assessments as (
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
        'http://adlnet.gov/expapi/verbs/attempted',
        'http://adlnet.gov/expapi/verbs/passed',
        'http://adlnet.gov/expapi/verbs/failed'
    )
)

select
    statement_id,
    school_id,
    actor->'account'->>'name'                                       as student_id,
    verb->>'id'                                                     as verb_id,
    object->>'id'                                                   as assessment_id,
    object->'definition'->'name'->>'en-US'                          as assessment_name,
    (result->'score'->>'raw')::numeric                              as score_raw,
    (result->'score'->>'min')::numeric                              as score_min,
    (result->'score'->>'max')::numeric                              as score_max,
    (result->'score'->>'scaled')::numeric                           as score_scaled,
    result->>'success'                                              as passed_str,
    result->>'duration'                                             as duration_iso,
    result->'extensions'->>'https://camara.org/xapi/activities/result/completion-status' as completion_status,
    context->'extensions'->'https://camara.org/xapi/context'->>'subject_id'      as subject_id,
    context->'extensions'->'https://camara.org/xapi/context'->>'attempt_number'  as attempt_number_str,
    context->'extensions'->'https://camara.org/xapi/context'->>'platform_id'     as platform_id,
    context->'extensions'->'https://camara.org/xapi/context'->>'is_offline'      as is_offline_str,
    timestamp::timestamptz                                          as event_timestamp,
    event_fingerprint
from raw_assessments
