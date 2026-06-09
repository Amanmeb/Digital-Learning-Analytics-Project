-- Calculates SHA-256 fingerprint for deduplication
-- Matches the Python fingerprint calculation in xapi/validator.py
-- Formula: SHA-256 of student_id|event_type|content_id|timestamp|school_id

{% macro calculate_fingerprint(student_id, event_type, content_id, timestamp, school_id) %}
    encode(
        digest(
            {{ student_id }} || '|' ||
            {{ event_type }} || '|' ||
            {{ content_id }} || '|' ||
            {{ timestamp }} || '|' ||
            {{ school_id }},
            'sha256'
        ),
        'hex'
    )
{% endmacro %}
