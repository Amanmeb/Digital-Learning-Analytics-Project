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

    # 1. Clean up extra table if created
    cur.execute("DROP TABLE IF EXISTS ops.users;")
    conn.commit()

    # 2. Seed mart.dim_role in existing schema
    roles = [
        ("ROLE_ADMIN", "Super Admin"),
        ("ROLE_REGIONAL", "Regional Admin"),
        ("ROLE_TEACHER", "Teacher"),
    ]
    for r_id, r_name in roles:
        cur.execute("""
            INSERT INTO mart.dim_role (role_id, role_name)
            VALUES (%s, %s)
            ON CONFLICT (role_id) DO UPDATE SET role_name = EXCLUDED.role_name;
        """, (r_id, r_name))
    conn.commit()

    # 3. Seed Admin and Regional users into existing mart.dim_teacher table
    accounts = [
        ("admin@camara.org", "ET-AA-001", "F", "Master", "System Administrator", "ROLE_ADMIN"),
        ("amhara@camara.org", "ET-AM-001", "M", "Bachelor", "Amhara Regional Lead", "ROLE_REGIONAL"),
        ("oromia@camara.org", "ET-OR-001", "F", "Bachelor", "Oromia Regional Lead", "ROLE_REGIONAL"),
        ("snnpr@camara.org", "ET-SN-001", "M", "Bachelor", "SNNPR Regional Lead", "ROLE_REGIONAL"),
        ("tigray@camara.org", "ET-TI-001", "M", "Bachelor", "Tigray Regional Lead", "ROLE_REGIONAL"),
    ]

    for t_id, sch_id, gen, edu, field, role in accounts:
        cur.execute("""
            INSERT INTO mart.dim_teacher (teacher_id, school_id, gender, education_level, field_of_study, role_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (teacher_id) DO UPDATE SET
                school_id = EXCLUDED.school_id,
                role_id = EXCLUDED.role_id,
                field_of_study = EXCLUDED.field_of_study;
        """, (t_id, sch_id, gen, edu, field, role))

    conn.commit()
    print("Populated mart.dim_role and mart.dim_teacher in existing schema successfully!")

    # Verify
    cur.execute("""
        SELECT t.teacher_id, r.role_name, s.school_name, r.role_id
        FROM mart.dim_teacher t
        JOIN mart.dim_role r ON t.role_id = r.role_id
        LEFT JOIN mart.dim_school s ON t.school_id = s.school_id;
    """)
    rows = cur.fetchall()
    print("Registered Admin & Regional accounts in existing database schema:")
    for r in rows:
        print(f"  - {r[0]} -> {r[1]} ({r[2]})")

except Exception as e:
    print("Error seeding existing schema auth:", e)
