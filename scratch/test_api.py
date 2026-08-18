import psycopg2
import json

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="cdlaid_analytics",
        user="cdlaid_user",
        password="CdlaidDB2025!Strong"
    )
    cur = conn.cursor()

    # Query student count
    cur.execute("SELECT COUNT(*) FROM mart.dim_student;")
    students = cur.fetchone()[0]

    # Query schools count
    cur.execute("SELECT COUNT(*), COUNT(CASE WHEN last_sync_date >= CURRENT_DATE - INTERVAL '10 days' THEN 1 END) FROM mart.dim_school;")
    schools, synced = cur.fetchone()

    # Query xapi statements count
    cur.execute("SELECT COUNT(*) FROM raw.xapi_statements;")
    xapi_count = cur.fetchone()[0]

    # Query subjects count
    cur.execute("SELECT COUNT(*) FROM mart.dim_subject;")
    subjects_count = cur.fetchone()[0]

    print(json.dumps({
        "status": "success",
        "students": students,
        "schools": schools,
        "synced": synced,
        "xapi_count": xapi_count,
        "subjects": subjects_count
    }, indent=2))

except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))
