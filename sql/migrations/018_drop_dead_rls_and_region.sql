-- Migration 018
-- Removes the dead Postgres-native RLS system from migration 005 and
-- drops the old region_id / dim_region system, now fully replaced by
-- the geo_id hierarchy and the working Superset-native RLS built in
-- migrations 014-017.
--
-- The migration 005 policies and roles were never actually enforced --
-- Superset connects as cdlaid_user, which bypasses RLS entirely, and no
-- application code ever set the session variables those policies
-- depended on. They are dropped here rather than left in place, since
-- leaving them looks like working security when it never was.

-- Drop all RLS policies from migration 005
DROP POLICY IF EXISTS programme_team_session ON mart.fact_session;
DROP POLICY IF EXISTS donor_session ON mart.fact_session;
DROP POLICY IF EXISTS regional_manager_session ON mart.fact_session;
DROP POLICY IF EXISTS school_admin_session ON mart.fact_session;
DROP POLICY IF EXISTS teacher_session ON mart.fact_session;
DROP POLICY IF EXISTS technical_support_session ON mart.fact_session;
DROP POLICY IF EXISTS ai_specialist_session ON mart.fact_session;

DROP POLICY IF EXISTS programme_team_summary ON mart.fact_school_daily_summary;
DROP POLICY IF EXISTS donor_summary ON mart.fact_school_daily_summary;
DROP POLICY IF EXISTS regional_manager_summary ON mart.fact_school_daily_summary;
DROP POLICY IF EXISTS school_admin_summary ON mart.fact_school_daily_summary;

DROP POLICY IF EXISTS programme_team_student ON mart.dim_student;
DROP POLICY IF EXISTS regional_manager_student ON mart.dim_student;
DROP POLICY IF EXISTS school_admin_student ON mart.dim_student;
DROP POLICY IF EXISTS teacher_student ON mart.dim_student;

DROP POLICY IF EXISTS programme_team_school ON mart.dim_school;
DROP POLICY IF EXISTS donor_school ON mart.dim_school;
DROP POLICY IF EXISTS regional_manager_school ON mart.dim_school;
DROP POLICY IF EXISTS school_admin_school ON mart.dim_school;
DROP POLICY IF EXISTS technical_support_school ON mart.dim_school;

-- Disable RLS on these tables -- enforcement now happens entirely in
-- Superset via migrations 014-017, not at the Postgres level
ALTER TABLE mart.fact_session DISABLE ROW LEVEL SECURITY;
ALTER TABLE mart.fact_teacher_session DISABLE ROW LEVEL SECURITY;
ALTER TABLE mart.fact_content_usage DISABLE ROW LEVEL SECURITY;
ALTER TABLE mart.fact_ai_usage DISABLE ROW LEVEL SECURITY;
ALTER TABLE mart.fact_assessment_attempt DISABLE ROW LEVEL SECURITY;
ALTER TABLE mart.fact_school_daily_summary DISABLE ROW LEVEL SECURITY;
ALTER TABLE mart.dim_student DISABLE ROW LEVEL SECURITY;
ALTER TABLE mart.dim_school DISABLE ROW LEVEL SECURITY;

-- Revoke grants before dropping roles -- DROP ROLE fails if a role
-- still has active privileges on any object
REVOKE ALL ON ALL TABLES IN SCHEMA mart FROM role_programme_team, role_donor, role_regional_manager, role_school_admin, role_teacher, role_technical_support, role_ai_specialist;
REVOKE USAGE ON SCHEMA mart FROM role_programme_team, role_donor, role_regional_manager, role_school_admin, role_teacher, role_technical_support, role_ai_specialist;

-- Drop the unused Postgres roles from migration 005 -- nothing ever
-- connected as any of these
DROP ROLE IF EXISTS role_programme_team;
DROP ROLE IF EXISTS role_donor;
DROP ROLE IF EXISTS role_regional_manager;
DROP ROLE IF EXISTS role_school_admin;
DROP ROLE IF EXISTS role_teacher;
DROP ROLE IF EXISTS role_technical_support;
DROP ROLE IF EXISTS role_ai_specialist;

-- Now safe to drop the old region_id columns and dim_region table --
-- nothing references them anymore. dim_school.geo_id and dim_geo_node
-- fully replace this.
ALTER TABLE mart.dim_school DROP COLUMN IF EXISTS region_id;
ALTER TABLE mart.dim_content_provider DROP COLUMN IF EXISTS region_id;
DROP TABLE IF EXISTS mart.dim_region;