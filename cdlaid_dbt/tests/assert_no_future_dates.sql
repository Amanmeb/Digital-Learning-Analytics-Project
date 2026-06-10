-- Fails if any event timestamp is in the future
select *
from {{ ref("stg_sessions") }}
where event_timestamp > current_timestamp
