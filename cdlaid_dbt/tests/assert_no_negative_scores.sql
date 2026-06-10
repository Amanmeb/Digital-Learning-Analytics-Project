-- Fails if any assessment score is negative
select *
from {{ ref("stg_assessments") }}
where score_raw < 0
