-- Mart model for data completeness metadata
-- Shows last sync date, schools reporting today vs total
-- Referenced by all dashboards as a completeness indicator

with school_counts as (
    select
        count(*)                                        as total_active_schools,
        count(*) filter (
            where last_sync_date >= current_date - 1
        )                                               as schools_synced_recently,
        max(last_sync_date)                             as latest_sync_date
    from mart.dim_school
    where is_active = true
),

today_reporting as (
    select
        count(distinct school_id)                       as schools_reporting_today
    from {{ ref("core_school_summary") }}
    where summary_date = current_date
),

pipeline_health as (
    select
        count(*) filter (
            where status = 'ok'
        )::numeric / nullif(count(*), 0) * 100          as sync_health_pct,
        max(synced_at)                                  as last_sync_received
    from ops.sync_log
    where synced_at >= current_date - 1
)

select
    sc.total_active_schools,
    sc.schools_synced_recently,
    coalesce(tr.schools_reporting_today, 0)             as schools_reporting_today,
    sc.latest_sync_date,
    coalesce(ph.sync_health_pct, 0)                     as sync_health_pct,
    ph.last_sync_received,
    case
        when sc.total_active_schools > 0
        then round(
            coalesce(tr.schools_reporting_today, 0)::numeric
            / sc.total_active_schools * 100, 1
        )
        else 0
    end                                                 as reporting_coverage_pct,
    case
        when coalesce(tr.schools_reporting_today, 0) = sc.total_active_schools
        then 'Complete'
        when coalesce(tr.schools_reporting_today, 0) >= sc.total_active_schools * 0.8
        then 'Mostly Complete'
        when coalesce(tr.schools_reporting_today, 0) > 0
        then 'Partial'
        else 'No Data Today'
    end                                                 as completeness_status,
    current_timestamp                                   as refreshed_at
from school_counts sc
cross join today_reporting tr
left join pipeline_health ph on true