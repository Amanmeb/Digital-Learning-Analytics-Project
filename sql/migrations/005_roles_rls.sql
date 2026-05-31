-- Migration 005
-- PostgreSQL roles, RLS policies, and GRANT statements
-- CDLAID Analytics Platform

-- Create roles
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'role_programme_team')
        THEN CREATE ROLE role_programme_team;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'role_donor')
        THEN CREATE ROLE role_donor;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'role_regional_manager')
        THEN CREATE ROLE role_regional_manager;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'role_school_admin')
        THEN CREATE ROLE role_school_admin;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'role_teacher')
        THEN CREATE ROLE role_teacher;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'role_technical_support')
        THEN CREATE ROLE role_technical_support;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'role_ai_specialist')
        THEN CREATE ROLE role_ai_specialist;
    END IF;
END
$$;

-- Enable RLS on fact tables
ALTER TABLE mart.fact_session
    ENABLE ROW LEVEL SECURITY;
ALTER TABLE mart.fact_teacher_session
    ENABLE ROW LEVEL SECURITY;
ALTER TABLE mart.fact_content_usage
    ENABLE ROW LEVEL SECURITY;
ALTER TABLE mart.fact_ai_usage
    ENABLE ROW LEVEL SECURITY;
ALTER TABLE mart.fact_assessment_attempt
    ENABLE ROW LEVEL SECURITY;
ALTER TABLE mart.fact_school_daily_summary
    ENABLE ROW LEVEL SECURITY;
ALTER TABLE mart.dim_student
    ENABLE ROW LEVEL SECURITY;
ALTER TABLE mart.dim_school
    ENABLE ROW LEVEL SECURITY;

-- RLS policies for fact_session
CREATE POLICY programme_team_session ON mart.fact_session
    FOR SELECT TO role_programme_team USING (TRUE);

CREATE POLICY donor_session ON mart.fact_session
    FOR SELECT TO role_donor USING (TRUE);

CREATE POLICY regional_manager_session ON mart.fact_session
    FOR SELECT TO role_regional_manager
    USING (
        school_id IN (
            SELECT school_id FROM mart.dim_school
            WHERE region_id = current_setting('app.current_region_id', TRUE)
        )
    );

CREATE POLICY school_admin_session ON mart.fact_session
    FOR SELECT TO role_school_admin
    USING (
        school_id = current_setting('app.current_school_id', TRUE)
    );

CREATE POLICY teacher_session ON mart.fact_session
    FOR SELECT TO role_teacher
    USING (
        school_id = current_setting('app.current_school_id', TRUE)
    );

CREATE POLICY technical_support_session ON mart.fact_session
    FOR SELECT TO role_technical_support USING (TRUE);

CREATE POLICY ai_specialist_session ON mart.fact_session
    FOR SELECT TO role_ai_specialist USING (TRUE);

-- RLS policies for fact_school_daily_summary
CREATE POLICY programme_team_summary ON mart.fact_school_daily_summary
    FOR SELECT TO role_programme_team USING (TRUE);

CREATE POLICY donor_summary ON mart.fact_school_daily_summary
    FOR SELECT TO role_donor USING (TRUE);

CREATE POLICY regional_manager_summary ON mart.fact_school_daily_summary
    FOR SELECT TO role_regional_manager
    USING (
        school_id IN (
            SELECT school_id FROM mart.dim_school
            WHERE region_id = current_setting('app.current_region_id', TRUE)
        )
    );

CREATE POLICY school_admin_summary ON mart.fact_school_daily_summary
    FOR SELECT TO role_school_admin
    USING (
        school_id = current_setting('app.current_school_id', TRUE)
    );

-- RLS policies for dim_student
CREATE POLICY programme_team_student ON mart.dim_student
    FOR SELECT TO role_programme_team USING (TRUE);

CREATE POLICY regional_manager_student ON mart.dim_student
    FOR SELECT TO role_regional_manager
    USING (
        school_id IN (
            SELECT school_id FROM mart.dim_school
            WHERE region_id = current_setting('app.current_region_id', TRUE)
        )
    );

CREATE POLICY school_admin_student ON mart.dim_student
    FOR SELECT TO role_school_admin
    USING (
        school_id = current_setting('app.current_school_id', TRUE)
    );

CREATE POLICY teacher_student ON mart.dim_student
    FOR SELECT TO role_teacher
    USING (
        school_id = current_setting('app.current_school_id', TRUE)
    );

-- RLS policies for dim_school
CREATE POLICY programme_team_school ON mart.dim_school
    FOR SELECT TO role_programme_team USING (TRUE);

CREATE POLICY donor_school ON mart.dim_school
    FOR SELECT TO role_donor USING (TRUE);

CREATE POLICY regional_manager_school ON mart.dim_school
    FOR SELECT TO role_regional_manager
    USING (
        region_id = current_setting('app.current_region_id', TRUE)
    );

CREATE POLICY school_admin_school ON mart.dim_school
    FOR SELECT TO role_school_admin
    USING (
        school_id = current_setting('app.current_school_id', TRUE)
    );

CREATE POLICY technical_support_school ON mart.dim_school
    FOR SELECT TO role_technical_support USING (TRUE);

-- GRANT permissions
GRANT USAGE ON SCHEMA mart TO
    role_programme_team,
    role_donor,
    role_regional_manager,
    role_school_admin,
    role_teacher,
    role_technical_support,
    role_ai_specialist;

GRANT SELECT ON ALL TABLES IN SCHEMA mart TO
    role_programme_team,
    role_donor,
    role_regional_manager,
    role_school_admin,
    role_teacher,
    role_technical_support,
    role_ai_specialist;

GRANT USAGE ON SCHEMA raw TO cdlaid_user;
GRANT USAGE ON SCHEMA ops TO cdlaid_user;
GRANT USAGE ON SCHEMA core TO cdlaid_user;
GRANT USAGE ON SCHEMA mart TO cdlaid_user;
GRANT ALL ON ALL TABLES IN SCHEMA raw TO cdlaid_user;
GRANT ALL ON ALL TABLES IN SCHEMA ops TO cdlaid_user;
GRANT ALL ON ALL TABLES IN SCHEMA mart TO cdlaid_user;
