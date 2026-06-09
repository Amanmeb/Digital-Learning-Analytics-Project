-- Mart model for Data Quality and Pipeline Health dashboard
-- Internal use only -- Programme Team and Technical Support
-- Aggregates pipeline health metrics

with raw_stats as (
    select
        current_date                            as report_date,
        count(*) filter (
            where stored::date = current_date
        )                                       as records_today,
        count(*) filter (
            where stored::date = current_date
            and processed = true
        )                                       as records_processed_today,
        count(*) filter (
            where stored::date = current_date
            and processed = false
        )                                       as records_pending_today
    from raw.xapi_statements
),

sync_stats as (
    select
        count(*) filter (
            where synced_at::date = current_date
        )                                       as syncs_today,
        count(*) filter (
            where synced_at::date = current_date
            and status = 'ok'
        )                                       as successful_syncs_today,
        sum(statements_duplicate) filter (
            where synced_at::date = current_date
        )                                       as duplicates_rejected_today
    from ops.sync_log
),

import_stats as (
    select
        count(*) filter (
            where imported_at::date = current_date
        )                                       as imports_today,
        sum(rows_invalid) filter (
            where imported_at::date = current_date
        )                                       as invalid_rows_today
    from ops.manual_import_log
)

select
    r.report_date,
    r.records_today,
    r.records_processed_today,
    r.records_pending_today,
    s.syncs_today,
    s.successful_syncs_today,
    s.duplicates_rejected_today,
    i.imports_today,
    i.invalid_rows_today,
    current_timestamp                           as refreshed_at
from raw_stats r
cross join sync_stats s
cross join import_stats i
