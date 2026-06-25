-- Migration 010
-- Backfill pre-existing settings gap on school database
-- These already exist on central, missing on school since before this branch
-- Additive only -- ON CONFLICT DO NOTHING, no existing setting touched

INSERT INTO ops.settings (setting_key, setting_value, setting_scope, description) VALUES
    ('ai_control_group_min',     '10',      'global', 'Minimum students required for valid AI comparison'),
    ('auto_refresh',             'false',   'global', 'Dashboard auto-refresh on or off'),
    ('dashboard_language',       'English', 'global', 'Primary dashboard display language'),
    ('data_retention_audit_log', '1095',    'global', 'Days to retain audit log entries'),
    ('data_retention_raw_xapi',  '730',     'global', 'Days to retain raw xAPI statements'),
    ('early_dropoff_minutes',    '5',       'global', 'Minutes before session counted as early drop-off'),
    ('platform_risk_flag',       '0.4',     'global', 'Completion rate below this flags platform at risk'),
    ('provider_risk_flag',       '0.4',     'global', 'Completion rate below this flags provider at risk'),
    ('streak_long_days',         '14',      'global', 'Days for long streak threshold'),
    ('streak_medium_days',       '7',       'global', 'Days for medium streak threshold'),
    ('streak_short_days',        '3',       'global', 'Days for short streak threshold')
ON CONFLICT DO NOTHING;