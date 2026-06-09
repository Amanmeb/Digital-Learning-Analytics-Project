-- Returns a setting value from ops.settings table
-- Falls back to dbt variable if not found in database
-- Used by all core and mart models to read adjustable parameters

{% macro get_setting(key, default_value) %}
    coalesce(
        (
            select setting_value
            from ops.settings
            where setting_key = '{{ key }}'
            and setting_scope = 'global'
            limit 1
        ),
        '{{ default_value }}'
    )
{% endmacro %}
