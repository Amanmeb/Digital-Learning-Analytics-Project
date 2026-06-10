-- Normalizes a score to a 0-1 scale
-- Used in composite KPI calculations

{% macro normalize_score(score_column, min_val=0, max_val=100) %}
    case
        when {{ max_val }} - {{ min_val }} = 0 then 0
        else ({{ score_column }} - {{ min_val }}) / ({{ max_val }} - {{ min_val }})
    end
{% endmacro %}
