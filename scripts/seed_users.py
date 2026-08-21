import psycopg2
import os

db_host = os.environ.get("DB_HOST", "localhost")
db_port = int(os.environ.get("DB_PORT", "5432"))
db_name = os.environ.get("DB_NAME", "cdlaid_analytics")
db_user = os.environ.get("DB_USER", "cdlaid_user")
db_password = os.environ.get("DB_PASSWORD", "CdlaidDB2025!Strong")

print(f"Connecting to database {db_name} at {db_host}:{db_port}...")

try:
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_password
    )
    cur = conn.cursor()

    # 1. Create ops.users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ops.users (
            user_id VARCHAR(50) PRIMARY KEY,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            role VARCHAR(20) NOT NULL,
            display_name VARCHAR(100) NOT NULL,
            region VARCHAR(50),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)

    # 2. Insert user accounts
    users = [
        ("usr-001", "admin@camara.org", "camara123", "admin", "Admin User", None),
        ("usr-002", "amhara@camara.org", "regional123", "regional", "Amhara Regional Office", "Amhara"),
        ("usr-003", "oromia@camara.org", "regional123", "regional", "Oromia Regional Office", "Oromia"),
        ("usr-004", "snnpr@camara.org", "regional123", "regional", "SNNPR Regional Office", "SNNPR"),
        ("usr-005", "tigray@camara.org", "regional123", "regional", "Tigray Regional Office", "Tigray"),
        ("usr-006", "afar@camara.org", "regional123", "regional", "Afar Regional Office", "Afar"),
        ("usr-007", "gambella@camara.org", "regional123", "regional", "Gambella Regional Office", "Gambella"),
    ]

    for u_id, email, pwd, role, name, reg in users:
        cur.execute("""
            INSERT INTO ops.users (user_id, email, password_hash, role, display_name, region)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role,
                display_name = EXCLUDED.display_name,
                region = EXCLUDED.region;
        """, (u_id, email, pwd, role, name, reg))

    conn.commit()
    print("ops.users table created and seeded successfully!")

    # Verify
    cur.execute("SELECT COUNT(*) FROM ops.users;")
    count = cur.fetchone()[0]
    print(f"Total user records in PostgreSQL: {count}")

except Exception as e:
    print("Error seeding ops.users:", e)
