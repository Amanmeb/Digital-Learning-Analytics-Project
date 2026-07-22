-- Migration 016
-- Adds 4 new roles: Donor, Country Admin, Camara Global Admin, Woreda Officer
-- Woreda Officer requires widening the role_scope_settings scope_type
-- check constraint, since only self/school/region/country/all were
-- previously allowed

ALTER TABLE mart.role_scope_settings DROP CONSTRAINT role_scope_settings_scope_type_check;
ALTER TABLE mart.role_scope_settings ADD CONSTRAINT role_scope_settings_scope_type_check
    CHECK (scope_type::text = ANY (ARRAY['self', 'school', 'woreda', 'region', 'country', 'all']::text[]));

INSERT INTO mart.dim_role (role_id, role_name, is_active) VALUES
    ('ROL_DONOR', 'Donor', true),
    ('ROL_CADMIN', 'Country Admin', true),
    ('ROL_GLOBAL', 'Camara Global Admin', true),
    ('ROL_WOREDA', 'Woreda Officer', true)
ON CONFLICT (role_id) DO NOTHING;

-- Donor and Programme Officer are aggregate-only by nature (per role spec:
-- no individual student data) -- scope_type here still governs geo-level
-- visibility for aggregate dashboards; the individual-vs-aggregate
-- distinction is enforced separately via data_granularity in a later step
INSERT INTO mart.role_scope_settings (role_id, scope_type, is_default) VALUES
    ('ROL_DONOR', 'country', true),
    ('ROL_CADMIN', 'country', true),
    ('ROL_GLOBAL', 'all', true),
    ('ROL_WOREDA', 'woreda', true)
ON CONFLICT (role_id) DO NOTHING;