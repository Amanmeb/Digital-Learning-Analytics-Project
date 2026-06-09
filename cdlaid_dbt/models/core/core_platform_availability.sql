-- Core model for platform availability metrics
-- Tracks sync health and device usage patterns per school
-- Used by mart_device_infrastructure

with sync_health as (
    select
        school_id,
        date_trunc('day', synced_at)::date    as sync_date,
        count(*)                                as total_syncs,
        count(*) filter (where status = 'ok') as successful_syncs,
        avg(case when status = 'ok' then 1.0 else 0.0 end) * 100 as sync_health_pct
    from ops.sync_log
    group by school_id, date_trunc('day', synced_at)::date
)

select
    school_id,
    sync_date,
    total_syncs,
    successful_syncs,
    round(sync_health_pct::numeric, 2)          as sync_health_pct,
    case
        when sync_health_pct >= {{ var("sync_health_target") }}
        then 'ok'
        else 'below_target'
    end                                         as sync_status
from sync_health
