-- Migration 017
-- Adds a data granularity flag to the per-user scope table. Some roles
-- (Donor, Programme Officer, Regional Monitor per the role spec) must
-- never see individual student-level rows, regardless of their geo
-- scope -- only school/region/country aggregates. This is a separate
-- dimension from geo_id/is_all_access, which only controls WHICH
-- schools/regions/countries a user can see, not the granularity of
-- what they see within that scope.

ALTER TABLE ops.superset_user_scope
    ADD COLUMN IF NOT EXISTS data_granularity VARCHAR(20) NOT NULL DEFAULT 'individual';

ALTER TABLE ops.superset_user_scope
    ADD CONSTRAINT superset_user_scope_granularity_check
    CHECK (data_granularity IN ('individual', 'aggregate_only'));

-- Returns TRUE only if the user is allowed to see individual-level rows.
-- Used directly as the RLS clause on individual-level datasets --
-- aggregate_only users get zero rows there no matter what their geo
-- scope is.
CREATE OR REPLACE FUNCTION mart.can_see_individual_rows(p_user_id INTEGER)
RETURNS BOOLEAN AS $$
    SELECT coalesce(
        (SELECT data_granularity = 'individual' FROM ops.superset_user_scope
         WHERE superset_user_id = p_user_id),
        FALSE
    );
$$ LANGUAGE sql STABLE;