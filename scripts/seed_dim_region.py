import psycopg2
import os

db_host = os.environ.get("DB_HOST", "localhost")
db_port = int(os.environ.get("DB_PORT", "5432"))
db_name = os.environ.get("DB_NAME", "cdlaid_analytics")
db_user = os.environ.get("DB_USER", "cdlaid_user")
db_password = os.environ.get("DB_PASSWORD", "CdlaidDB2025!Strong")

print(f"Connecting to {db_name} at {db_host}:{db_port}...")

try:
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_password
    )
    cur = conn.cursor()

    # 1. Populate dim_region
    regions = [
        ("ET-AA", "Addis Ababa"),
        ("ET-OR", "Oromia"),
        ("ET-AM", "Amhara"),
        ("ET-TI", "Tigray"),
        ("ET-SN", "SNNPR"),
        ("ET-AF", "Afar"),
        ("ET-GA", "Gambella"),
        ("ET-BG", "Benishangul-Gumuz"),
        ("ET-SO", "Somali"),
        ("ET-HA", "Harari"),
    ]

    for r_id, r_name in regions:
        cur.execute("""
            INSERT INTO mart.dim_region (region_id, region_name)
            VALUES (%s, %s)
            ON CONFLICT (region_id) DO UPDATE SET region_name = EXCLUDED.region_name;
        """, (r_id, r_name))
    
    conn.commit()
    print("dim_region populated successfully!")

    # 2. Check current counts
    cur.execute("SELECT COUNT(*) FROM raw.xapi_statements;")
    xapi_c = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM mart.dim_student;")
    stud_c = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM mart.dim_school;")
    sch_c = cur.fetchone()[0]

    print(f"Summary Verification:\n  - xAPI statements: {xapi_c}\n  - Enrolled students: {stud_c}\n  - Schools: {sch_c}")

except Exception as e:
    print("Error seeding dim_region:", e)
