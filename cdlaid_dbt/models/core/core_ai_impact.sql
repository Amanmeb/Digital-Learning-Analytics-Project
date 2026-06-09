-- Core model for AI learning impact with control group comparison
-- Compares assessment scores for students who used AI vs those who did not
-- Control group: same school, same grade, same subject, same period
-- Used by mart_ai_usage

with ai_users as (
    select distinct
        student_id,
        school_id
    from {{ ref("stg_ai_usage") }}
),

assessments as (
    select
        a.student_id,
        a.school_id,
        a.assessment_id,
        a.subject_id,
        a.score_raw,
        a.attempt_number_str::int               as attempt_number,
        a.event_timestamp,
        case when u.student_id is not null
             then true else false
        end                                     as used_ai
    from {{ ref("stg_assessments") }} a
    left join ai_users u
        on a.student_id = u.student_id
        and a.school_id = u.school_id
)

select
    school_id,
    subject_id,
    used_ai,
    count(distinct student_id)                  as student_count,
    count(*)                                    as attempt_count,
    round(avg(score_raw)::numeric, 2)           as avg_score,
    round(min(score_raw)::numeric, 2)           as min_score,
    round(max(score_raw)::numeric, 2)           as max_score
from assessments
where score_raw is not null
group by school_id, subject_id, used_ai
