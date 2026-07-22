-- Mart model for AI Usage and Impact dashboard
-- Pre-aggregates AI usage metrics and control group comparison
-- Uses updated core_ai_impact with avg_score_pct and score improvement

with ai_summary as (
    select
        school_id,
        student_id,
        count(*)                                as total_interactions,
        count(distinct event_timestamp::date)   as active_days_with_ai,
        sum(
            case
                when duration_iso is not null
                then extract(epoch from duration_iso::interval) / 60
                else 0
            end
        )                                       as total_ai_minutes,
        count(distinct subject_id)              as subjects_covered,
        count(distinct query_type)              as query_types_used
    from {{ ref("stg_ai_usage") }}
    group by school_id, student_id
),

ai_impact_summary as (
    select
        school_id,
        subject_id,
        used_ai,
        student_count,
        avg_score_pct,
        avg_score_improvement_pct,
        is_valid_comparison
    from {{ ref("core_ai_impact") }}
),

ai_vs_no_ai as (
    select
        school_id,
        subject_id,
        max(case when used_ai then avg_score_pct else null end)             as ai_avg_score_pct,
        max(case when not used_ai then avg_score_pct else null end)         as no_ai_avg_score_pct,
        max(case when used_ai then avg_score_improvement_pct else null end) as ai_score_improvement_pct,
        max(case when used_ai then student_count else 0 end)                as ai_student_count,
        max(case when not used_ai then student_count else 0 end)            as no_ai_student_count,
        bool_or(is_valid_comparison)                                        as is_valid_comparison
    from ai_impact_summary
    group by school_id, subject_id
)

select
    s.school_id,
    s.student_id,
    s.total_interactions,
    s.active_days_with_ai,
    round(s.total_ai_minutes::numeric, 2)       as total_ai_minutes,
    round(s.total_ai_minutes / 60.0, 4)         as total_ai_hours,
    s.subjects_covered,
    s.query_types_used,
    current_timestamp                           as refreshed_at
from ai_summary s