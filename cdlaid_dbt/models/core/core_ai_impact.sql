-- Core model for AI learning impact with control group comparison
-- Compares assessment scores for students who used AI vs those who did not
-- Control group: same school, same subject, same period
-- Includes score improvement from first to latest attempt
-- ai_control_group_min setting controls minimum students for valid comparison

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
        a.score_max,
        case
            when a.score_max > 0
            then round(a.score_raw::numeric / a.score_max * 100, 2)
            else null
        end                                     as score_pct,
        a.attempt_number_str::int               as attempt_number,
        a.event_timestamp,
        case when u.student_id is not null
             then true else false
        end                                     as used_ai
    from {{ ref("stg_assessments") }} a
    left join ai_users u
        on a.student_id = u.student_id
        and a.school_id = u.school_id
    where a.score_raw is not null
      and a.score_max > 0
),

first_and_last as (
    select
        student_id,
        school_id,
        subject_id,
        used_ai,
        first_value(score_pct) over (
            partition by student_id, school_id, subject_id
            order by attempt_number, event_timestamp
        )                                       as first_score_pct,
        last_value(score_pct) over (
            partition by student_id, school_id, subject_id
            order by attempt_number, event_timestamp
            rows between unbounded preceding and unbounded following
        )                                       as last_score_pct,
        score_pct,
        attempt_number,
        event_timestamp
    from assessments
),

improvement as (
    select
        student_id,
        school_id,
        subject_id,
        used_ai,
        avg(score_pct)                          as avg_score_pct,
        max(first_score_pct)                    as first_score_pct,
        max(last_score_pct)                     as last_score_pct,
        max(last_score_pct) - max(first_score_pct) as score_improvement_pct,
        count(*)                                as attempt_count
    from first_and_last
    group by student_id, school_id, subject_id, used_ai
),

summary as (
    select
        school_id,
        subject_id,
        used_ai,
        count(distinct student_id)              as student_count,
        sum(attempt_count)                      as total_attempts,
        round(avg(avg_score_pct)::numeric, 2)   as avg_score_pct,
        round(avg(score_improvement_pct)::numeric, 2) as avg_score_improvement_pct,
        round(avg(first_score_pct)::numeric, 2) as avg_first_score_pct,
        round(avg(last_score_pct)::numeric, 2)  as avg_last_score_pct
    from improvement
    group by school_id, subject_id, used_ai
)

select
    s.school_id,
    s.subject_id,
    s.used_ai,
    s.student_count,
    s.total_attempts,
    s.avg_score_pct,
    s.avg_score_improvement_pct,
    s.avg_first_score_pct,
    s.avg_last_score_pct,
    case
        when s.student_count >= {{ get_setting("ai_control_group_min") | int }}
        then true
        else false
    end                                         as is_valid_comparison,
    current_timestamp                           as refreshed_at
from summary s