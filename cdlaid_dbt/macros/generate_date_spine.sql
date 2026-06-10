-- Generates a date spine between two dates
-- Used in trend calculations to fill gaps in data

{% macro generate_date_spine(start_date, end_date) %}
    select
        generate_series(
            {{ start_date }}::date,
            {{ end_date }}::date,
            '1 day'::interval
        )::date as date_day
{% endmacro %}
