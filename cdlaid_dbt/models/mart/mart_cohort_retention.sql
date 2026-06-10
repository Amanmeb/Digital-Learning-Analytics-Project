-- Mart model for cohort retention analysis
-- Groups students by first session month
-- Tracks how many returned in subsequent months
-- Used by Student Engagement dashboard

with first_sessions as (
    select
        student_id,
        school_id,
        min(session_date)                       as first_session_date,
        date_trunc('month', min(session_date))::date as cohort_month
    from {{ ref("core_student_engagement") }}
    group by student_id, school_id
),

monthly_activity as (
    select
        student_id,
        school_id,
        date_trunc('month', session_date)::date as activity_month
    from {{ ref("core_student_engagement") }}
    group by student_id, school_id, date_trunc('month', session_date)::date
),

cohort_activity as (
    select
        f.school_id,
        f.cohort_month,
        m.activity_month,
        count(distinct f.student_id)            as active_students,
        extract(year from age(m.activity_month::timestamp, f.cohort_month::timestamp)) * 12
        + extract(month from age(m.activity_month::timestamp, f.cohort_month::timestamp))
                                                as months_since_cohort_start
    from first_sessions f
    join monthly_activity m
        on f.student_id = m.student_id
        and f.school_id = m.school_id
    group by f.school_id, f.cohort_month, m.activity_month
),

cohort_size as (
    select
        school_id,
        cohort_month,
        count(distinct student_id)              as cohort_size
    from first_sessions
    group by school_id, cohort_month
)

select
    ca.school_id,
    ca.cohort_month,
    cs.cohort_size,
    ca.activity_month,
    ca.months_since_cohort_start,
    ca.active_students,
    case
        when cs.cohort_size > 0
        then round(ca.active_students::numeric / cs.cohort_size * 100, 2)
        else 0
    end                                         as retention_rate_pct,
    current_timestamp                           as refreshed_at
from cohort_activity ca
join cohort_size cs
    on ca.school_id = cs.school_id
    and ca.cohort_month = cs.cohort_month
order by ca.school_id, ca.cohort_month, ca.activity_month