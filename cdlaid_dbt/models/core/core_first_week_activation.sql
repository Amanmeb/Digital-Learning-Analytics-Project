-- Core model for first week activation rate
-- Checks if students logged in within first_week_days of registration
-- Used by mart_student_engagement

with students as (
    select
        student_id,
        school_id,
        registration_date
    from mart.dim_student
    where is_active = true
    and registration_date is not null
),

first_sessions as (
    select
        student_id,
        school_id,
        min(session_date)                       as first_session_date
    from {{ ref("core_student_engagement") }}
    group by student_id, school_id
)

select
    s.student_id,
    s.school_id,
    s.registration_date,
    f.first_session_date,
    case
        when f.first_session_date is not null
        and (f.first_session_date - s.registration_date) <= {{ var("first_week_days") }}
        then true
        else false
    end                                         as activated_in_first_week,
    case
        when f.first_session_date is not null
        then (f.first_session_date - s.registration_date)
        else null
    end                                         as days_to_first_session
from students s
left join first_sessions f
    on s.student_id = f.student_id
    and s.school_id = f.school_id
