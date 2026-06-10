-- Fails if any fingerprint appears more than once in raw statements
select event_fingerprint, count(*) as cnt
from raw.xapi_statements
where event_fingerprint is not null
group by event_fingerprint
having count(*) > 1
