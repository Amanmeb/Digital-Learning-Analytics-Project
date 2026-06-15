-- Core model for learning consistency metrics
-- Calculates streak distribution and active day ratios
-- Streak thresholds read from ops.settings
-- Used by mart_student_engagement

with daily_activity as (
    select
        student_id,
        school_id,
        session_date,
        sum(session_count)                      as daily_sessions
    from {{ ref("core_student_engagement") }}
    group by student_id, school_id, session_date
),

date_range as (
    select
        student_id,
        school_id,
        min(session_date)                       as first_active_date,
        max(session_date)                       as last_active_date,
        count(distinct session_date)            as active_days,
        max(session_date) - min(session_date) + 1 as total_days_span
    from daily_activity
    group by student_id, school_id
),

consecutive as (
    select
        student_id,
        school_id,
        session_date,
        session_date - (row_number() over (
            partition by student_id, school_id
            order by session_date
        ))::int * interval '1 day'            as streak_group
    from daily_activity
),

streaks as (
    select
        student_id,
        school_id,
        streak_group,
        count(*)                                as streak_length
    from consecutive
    group by student_id, school_id, streak_group
),

max_streak as (
    select
        student_id,
        school_id,
        max(streak_length)                      as longest_streak_days
    from streaks
    group by student_id, school_id
)

select
    dr.student_id,
    dr.school_id,
    dr.first_active_date,
    dr.last_active_date,
    dr.active_days,
    dr.total_days_span,
    case
        when dr.total_days_span > 0
        then round(dr.active_days::numeric / dr.total_days_span, 4)
        else 0
    end                                         as consistency_score,
    coalesce(ms.longest_streak_days, 0)         as longest_streak_days,
    case
        when coalesce(ms.longest_streak_days, 0) >= {{ get_setting("streak_long_days") | int }}
        then 'long'
        when coalesce(ms.longest_streak_days, 0) >= {{ get_setting("streak_medium_days") | int }}
        then 'medium'
        when coalesce(ms.longest_streak_days, 0) >= {{ get_setting("streak_short_days") | int }}
        then 'short'
        else 'none'
    end                                         as streak_tier
from date_range dr
left join max_streak ms
    on dr.student_id = ms.student_id
    and dr.school_id = ms.school_id