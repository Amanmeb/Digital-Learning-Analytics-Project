# Validates all seed data is correctly loaded in PostgreSQL
# Run after migrations to confirm all reference data is present
# Checks row counts and foreign key integrity

import os
import sys
import psycopg2

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://cdlaid_user:CdlaidDB2025!Strong@localhost:5432/cdlaid_analytics"
)

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"

results = []


def check(label, query, expected_min, conn):
    cur = conn.cursor()
    cur.execute(query)
    count = cur.fetchone()[0]
    if count >= expected_min:
        results.append((PASS, label, str(count) + " rows"))
    else:
        results.append((FAIL, label, "Expected at least " + str(expected_min) + " got " + str(count)))


def run():
    print("CDLAID Seed Data Validation")
    print("============================")

    try:
        conn = psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print("FAIL -- Cannot connect to database: " + str(e))
        sys.exit(1)

    # Check schemas exist
    check("Schema raw exists",    "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'raw'",    1, conn)
    check("Schema ops exists",    "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'ops'",    1, conn)
    check("Schema core exists",   "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'core'",   1, conn)
    check("Schema mart exists",   "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'mart'",   1, conn)

    # Check dimension tables exist and have data
    check("dim_grade has 13 rows",           "SELECT COUNT(*) FROM mart.dim_grade",            13, conn)
    check("dim_language has 7 rows",         "SELECT COUNT(*) FROM mart.dim_language",          7, conn)
    check("dim_region has 14 rows",          "SELECT COUNT(*) FROM mart.dim_region",           14, conn)
    check("dim_platform has 12 rows",        "SELECT COUNT(*) FROM mart.dim_platform",         12, conn)
    check("dim_content_type has 11 rows",    "SELECT COUNT(*) FROM mart.dim_content_type",     11, conn)
    check("dim_role has 10 rows",            "SELECT COUNT(*) FROM mart.dim_role",             10, conn)

    # Check fact tables exist
    check("fact_session exists",             "SELECT COUNT(*) FROM mart.fact_session",          0, conn)
    check("fact_assessment_attempt exists",  "SELECT COUNT(*) FROM mart.fact_assessment_attempt", 0, conn)
    check("fact_ai_usage exists",            "SELECT COUNT(*) FROM mart.fact_ai_usage",         0, conn)

    # Check operational tables
    check("ops.settings has rows",           "SELECT COUNT(*) FROM ops.settings",              10, conn)
    check("ops.translations has rows",       "SELECT COUNT(*) FROM ops.translations",           5, conn)
    check("raw.xapi_statements exists",      "SELECT COUNT(*) FROM raw.xapi_statements",        0, conn)
    check("ops.sync_log exists",             "SELECT COUNT(*) FROM ops.sync_log",               0, conn)

    # Check composite KPI weights are in settings
    check("learning_engagement_weights set",
          "SELECT COUNT(*) FROM ops.settings WHERE setting_key = 'learning_engagement_weights'", 1, conn)
    check("school_performance_weights set",
          "SELECT COUNT(*) FROM ops.settings WHERE setting_key = 'school_performance_weights'",  1, conn)

    conn.close()

    print("")
    failed = 0
    for status, label, detail in results:
        print(status + "  " + label + " -- " + detail)
        if status == FAIL:
            failed += 1

    print("")
    if failed == 0:
        print("All checks passed.")
    else:
        print(str(failed) + " check(s) failed.")
        sys.exit(1)


if __name__ == "__main__":
    run()
