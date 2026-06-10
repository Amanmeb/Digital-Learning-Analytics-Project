-- Mart model for Equity and Inclusion dashboard
-- Pre-aggregates gender parity and SNE participation metrics

with equity as (
    select
        school_id,
        gender,
        has_special_needs,
        special_need_type,
        total_students,
        active_students,
        participation_rate_pct
    from {{ ref("core_equity") }}
),

gender_summary as (
    select
        school_id,
        sum(active_students) filter (where gender = 'Female')   as active_female,
        sum(active_students) filter (where gender = 'Male')     as active_male,
        sum(total_students) filter (where gender = 'Female')    as total_female,
        sum(total_students) filter (where gender = 'Male')      as total_male
    from equity
    group by school_id
)

select
    g.school_id,
    g.active_female,
    g.active_male,
    g.total_female,
    g.total_male,
    case
        when g.active_male > 0
        then round(g.active_female::numeric / g.active_male, 4)
        else null
    end                                         as gender_parity_index,
    case
        when g.active_male > 0
        and round(g.active_female::numeric / g.active_male, 4) between {{ var("gender_parity_min") }} and {{ var("gender_parity_max") }}
        then 'OK'
        else 'REVIEW'
    end                                         as gpi_status,
    current_timestamp                           as refreshed_at
from gender_summary g
