with syncs as (

    select *
    from mart.fact_sync_health

)

select
    school_id,
    date_key,

    count(*) as total_syncs,

    count(*) filter (where status = 'SUCCESS') as successful_syncs,

    round(
        100.0 *
        count(*) filter (where status='SUCCESS')
        /
        nullif(count(*),0),
        2
    ) as sync_health_pct,

    avg(sync_duration_secs) as avg_sync_duration

from syncs
group by school_id, date_key