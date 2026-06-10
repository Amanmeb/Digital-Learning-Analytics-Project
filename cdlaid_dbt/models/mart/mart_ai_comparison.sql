-- Mart model for AI vs No-AI score comparison
-- One row per school per subject showing AI users vs control group
-- Used by AI Usage and Impact dashboard comparison chart

select
    school_id,
    subject_id,
    max(case when used_ai then avg_score_pct else null end)             as ai_avg_score_pct,
    max(case when not used_ai then avg_score_pct else null end)         as no_ai_avg_score_pct,
    max(case when used_ai then avg_score_pct else null end)
    - max(case when not used_ai then avg_score_pct else null end)       as score_difference_pct,
    max(case when used_ai then avg_score_improvement_pct else null end) as ai_score_improvement_pct,
    max(case when used_ai then student_count else 0 end)                as ai_student_count,
    max(case when not used_ai then student_count else 0 end)            as no_ai_student_count,
    max(case when used_ai then total_attempts else 0 end)               as ai_total_attempts,
    max(case when not used_ai then total_attempts else 0 end)           as no_ai_total_attempts,
    bool_or(is_valid_comparison)                                        as is_valid_comparison,
    current_timestamp                                                   as refreshed_at
from {{ ref("core_ai_impact") }}
group by school_id, subject_id