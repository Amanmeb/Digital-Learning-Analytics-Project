-- Fails if any sync log entry has an invalid status
select *
from ops.sync_log
where status not in ('ok', 'failed', 'partial')
