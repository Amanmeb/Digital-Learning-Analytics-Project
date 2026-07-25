-- Mart model for Platform Analytics dashboard
-- Pre-aggregates platform usage, availability, device utilisation,
-- content completion, and AI usage metrics.

with platform_usage as (

    select
        c.school_id,
        c.platform_id,
        d.date_key,

        count(distinct c.student_id)                         as unique_students,
        sum(c.session_count)                                 as total_sessions,
        round(avg(c.avg_session_duration_minutes)::numeric, 2) as avg_session_minutes,
        round(sum(c.total_session_minutes)::numeric, 2)      as total_minutes,
        count(*) filter (where c.is_offline)                 as offline_sessions

    from {{ ref("core_student_engagement") }} c

    join mart.dim_date d
        on c.session_date = d.full_date

    group by
        c.school_id,
        c.platform_id,
        d.date_key

),

platform_content as (

    select
        school_id,
        platform_id,
        date_key,

        count(*)                                             as total_content_accesses,
        sum(completed_count)                                 as total_completed,

        case
            when count(*) > 0
                then round(sum(completed_count)::numeric / count(*) * 100, 2)
            else 0
        end                                                  as completion_rate_pct

    from {{ ref("core_content_performance") }}

    group by
        school_id,
        platform_id,
        date_key

),

platform_ai as (

    select
        school_id,
        platform_id,
        date_key,

        count(*)                                             as total_ai_queries,
        count(distinct student_id)                           as students_used_ai

    from {{ ref("stg_ai_usage") }}

    group by
        school_id,
        platform_id,
        date_key

)

select
    u.school_id,
    u.platform_id,
    u.date_key,

    p.platform_name,
    p.platform_type,
    p.tracking_depth,

    u.unique_students,
    u.total_sessions,
    u.avg_session_minutes,
    u.total_minutes,
    u.offline_sessions,

    ph.sync_health_pct,
    ph.total_syncs,
    ph.successful_syncs,

    du.active_devices,
    du.avg_usage_minutes,
    du.total_usage_minutes,

    pc.total_content_accesses,
    pc.total_completed,
    pc.completion_rate_pct,

    pa.total_ai_queries,
    pa.students_used_ai,

    case
        when u.total_sessions > 0
            then round(u.offline_sessions::numeric / u.total_sessions * 100, 2)
        else 0
    end                                                      as offline_pct,

    current_timestamp                                        as refreshed_at

from platform_usage u

join mart.dim_platform p
    on u.platform_id = p.platform_id

-- left join {{ ref("core_platform_availability") }} ph
--     on ph.school_id = u.school_id
--    and ph.date_key = u.date_key
left join mart.dim_date dd
    on dd.date_key = u.date_key

left join {{ ref("core_platform_availability") }} ph
    on ph.school_id = u.school_id
   and ph.sync_date = dd.full_date

left join {{ ref("core_device_utilization") }} du
    on du.school_id = u.school_id
   and du.date_key = u.date_key

left join platform_content pc
    on pc.school_id = u.school_id
   and pc.platform_id = u.platform_id
   and pc.date_key = u.date_key

left join platform_ai pa
    on pa.school_id = u.school_id
   and pa.platform_id = u.platform_id
   and pa.date_key = u.date_key
