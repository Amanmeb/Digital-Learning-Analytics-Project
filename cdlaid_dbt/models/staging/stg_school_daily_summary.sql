{{ config(materialized='view') }}

select *
from mart.fact_school_daily_summary


-- {{ config(materialized='view') }}

-- select
--     school_id,
--     date_key,
--     active_students,
--     active_teachers,
--     total_sessions,
--     total_learning_minutes,
--     total_ai_queries,
--     total_content_accesses,
--     offline_sessions
-- from mart.fact_school_daily_summary