-- Core model for equity and inclusion metrics
-- Calculates gender parity index and SNE participation
-- Used by mart_equity_inclusion

with students as (
    select
        s.student_id,
        s.school_id,
        s.gender,
        s.has_special_needs,
        s.special_need_type,
        s.grade_id
    from mart.dim_student s
    where s.is_active = true
),

active_students as (
    select distinct
        student_id,
        school_id
    from {{ ref("core_student_engagement") }}
),

student_activity as (
    select
        s.student_id,
        s.school_id,
        s.gender,
        s.has_special_needs,
        s.special_need_type,
        case when a.student_id is not null then true else false end as is_active
    from students s
    left join active_students a
        on s.student_id = a.student_id
        and s.school_id = a.school_id
)

select
    school_id,
    gender,
    has_special_needs,
    special_need_type,
    count(*)                                            as total_students,
    count(*) filter (where is_active)                   as active_students,
    case
        when count(*) > 0
        then round((count(*) filter (where is_active))::numeric / count(*) * 100, 2)
        else 0
    end                                                 as participation_rate_pct
from student_activity
group by school_id, gender, has_special_needs, special_need_type
