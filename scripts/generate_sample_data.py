import psycopg2
import random
import uuid
import hashlib
from datetime import datetime, timedelta, timezone
import json

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="cdlaid_analytics",
    user="cdlaid_user",
    password="CdlaidDB2025!Strong"
)
cur = conn.cursor()
print("Connected to database")

def fp(student_id, event_type, content_id, timestamp, school_id):
    raw = student_id + "|" + event_type + "|" + content_id + "|" + str(timestamp) + "|" + school_id
    return hashlib.sha256(raw.encode()).hexdigest()

def rand_date(days_ago_start, days_ago_end=0):
    start = datetime.now(timezone.utc) - timedelta(days=days_ago_start)
    end = datetime.now(timezone.utc) - timedelta(days=days_ago_end)
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))

def school_hour(base):
    hour = random.choices(range(7, 18), weights=[1,2,4,5,5,4,3,2,2,2,1], k=1)[0]
    return base.replace(hour=hour, minute=random.randint(0,59), second=random.randint(0,59))

# ------------------------------------------------------------
# CLEAR EXISTING DATA
# Removes all previously generated sample data before regenerating
# Dimension tables use ON CONFLICT DO NOTHING so no need to clear those
# ------------------------------------------------------------
print("Clearing existing xAPI statements and derived data...")
cur.execute("DELETE FROM raw.xapi_statements")
cur.execute("DELETE FROM ops.sync_log")
cur.execute("TRUNCATE mart.fact_session CASCADE")
cur.execute("TRUNCATE mart.fact_content_usage CASCADE")
cur.execute("TRUNCATE mart.fact_assessment_attempt CASCADE")
cur.execute("TRUNCATE mart.fact_ai_usage CASCADE")
cur.execute("TRUNCATE mart.fact_school_daily_summary CASCADE")
cur.execute("TRUNCATE mart.fact_device_usage CASCADE")
cur.execute("TRUNCATE mart.fact_sync_health CASCADE")
conn.commit()
print("Existing data cleared")

# ------------------------------------------------------------
# REGIONS
# ------------------------------------------------------------
print("Regions now come from mart.dim_geo_node -- dim_region was dropped, skipping")

# ------------------------------------------------------------
# GRADES
# ------------------------------------------------------------
print("Inserting grades...")
for i in range(1, 13):
    gid = "GR" + str(i).zfill(2)
    cur.execute("""
        INSERT INTO mart.dim_grade (grade_id, grade_level, grade_label)
        VALUES (%s, %s, %s) ON CONFLICT (grade_id) DO NOTHING
    """, (gid, i, "Grade " + str(i)))
conn.commit()
print("Grades done")

# ------------------------------------------------------------
# SUBJECTS
# ------------------------------------------------------------
print("Inserting subjects...")
subjects_data = [
    ("SUB001","Mathematics"),("SUB002","English"),("SUB003","Amharic"),
    ("SUB004","General Science"),("SUB005","Biology"),("SUB006","Chemistry"),
    ("SUB007","Physics"),("SUB008","Social Studies"),("SUB009","History"),
    ("SUB010","Geography"),("SUB011","ICT and Computing"),("SUB012","Physical Education"),
]
for s in subjects_data:
    cur.execute("""
        INSERT INTO mart.dim_subject (subject_id, subject_name)
        VALUES (%s, %s) ON CONFLICT (subject_id) DO NOTHING
    """, s)
conn.commit()
print("Subjects done")

# ------------------------------------------------------------
# LANGUAGES
# ------------------------------------------------------------
print("Inserting languages...")
languages_data = [
    ("LANG001","English"),("LANG002","Amharic"),
    ("LANG003","Afan Oromo"),("LANG004","Tigrinya"),("LANG005","Somali"),
]
for l in languages_data:
    cur.execute("""
        INSERT INTO mart.dim_language (language_id, language_name)
        VALUES (%s, %s) ON CONFLICT (language_id) DO NOTHING
    """, l)
conn.commit()
print("Languages done")

# ------------------------------------------------------------
# CONTENT TYPES
# ------------------------------------------------------------
print("Inserting content types...")
content_types_data = [
    ("CT001","Video"),("CT002","Quiz"),("CT003","Game"),
    ("CT004","Reading"),("CT005","Simulation"),("CT006","Exercise"),
]
for ct in content_types_data:
    cur.execute("""
        INSERT INTO mart.dim_content_type (content_type_id, content_type_name)
        VALUES (%s, %s) ON CONFLICT (content_type_id) DO NOTHING
    """, ct)
conn.commit()
print("Content types done")

# ------------------------------------------------------------
# PROVIDERS
# ------------------------------------------------------------
print("Inserting providers...")
providers_data = [
    ("PROV001","Ministry of Education Ethiopia","Government",True,False,True),
    ("PROV002","Camara Education","NGO",False,True,True),
    ("PROV003","PhET University of Colorado","University",True,False,False),
    ("PROV004","Rachel","NGO",False,False,True),
    ("PROV005","H5P","Open Source",True,False,True),
]
for p in providers_data:
    cur.execute("""
        INSERT INTO mart.dim_content_provider
            (provider_id, provider_name, provider_type,
             is_content_owner, is_funder, is_distributor)
        VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (provider_id) DO NOTHING
    """, p)
conn.commit()
print("Providers done")

# ------------------------------------------------------------
# PLATFORMS
# ------------------------------------------------------------
print("Inserting platforms...")
platforms_data = [
    ("PLT_OA","Offline Academy","offline","xapi_custom","full",False),
    ("PLT_CS","Camara Studio","offline","xapi_custom","full",True),
    ("PLT_GAME","Game Apps","offline","xapi_custom","full",False),
    ("PLT_H5P","H5P","offline","xapi_native","full",False),
    ("PLT_PHET","PhET Simulations","offline","scorm","partial",False),
    ("PLT_RACHEL","Rachel","offline","url_only","click_only",False),
    ("PLT_SCORM","SCORM Package","offline","scorm","partial",False),
]
for p in platforms_data:
    cur.execute("""
        INSERT INTO mart.dim_platform
            (platform_id, platform_name, platform_type,
             tracking_method, tracking_depth, has_ai, is_offline)
        VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (platform_id) DO NOTHING
    """, (p[0],p[1],p[2],p[3],p[4],p[5],True))
conn.commit()
print("Platforms done")

# ------------------------------------------------------------
# AI SERVICE
# ------------------------------------------------------------
print("Inserting AI service...")
cur.execute("""
    INSERT INTO mart.dim_ai_service
        (ai_service_id, ai_type, ai_scope, ai_mode, description)
    VALUES ('AI001','Generative','Subject','interactive','Camara AI Tutor')
    ON CONFLICT (ai_service_id) DO NOTHING
""")
conn.commit()
print("AI service done")

# ------------------------------------------------------------
# SCHOOLS
# Schools have staggered sync dates to test sync health KPIs
# Schools 5, 7, 10 have stale sync dates (8, 10, 16 days)
# ------------------------------------------------------------
print("Inserting schools...")
schools_data = [
    ("ET-AA-001","Addis Ababa Primary School","ET-AA","Bole","Addis Ababa","Government","Primary",8.9806,38.7578,650,320,330,45,28),
    ("ET-AA-002","Kirkos Secondary School","ET-AA","Kirkos","Addis Ababa","Private","Secondary",9.0054,38.7636,420,210,210,30,18),
    ("ET-AA-003","Camara NGO School Addis","ET-AA","Yeka","Addis Ababa","NGO-run","Primary",9.0272,38.8013,380,195,185,55,22),
    ("ET-OR-001","Adama Community School","ET-OR","Adama Zone","Adama","Government","Primary",8.5400,39.2700,720,365,355,60,32),
    ("ET-OR-002","Jimma Private Academy","ET-OR","Jimma Zone","Jimma","Private","Secondary",7.6600,36.8300,290,145,145,20,15),
    ("ET-AM-001","Bahir Dar Government School","ET-AM","West Gojjam","Bahir Dar","Government","Primary",11.5900,37.3900,810,410,400,70,38),
    ("ET-AM-002","Gondar Special Needs School","ET-AM","North Gondar","Gondar","Special needs school","Primary",12.6000,37.4600,210,105,105,80,20),
    ("ET-TI-001","Mekelle Religious School","ET-TI","Central Tigray","Mekelle","Religious","Secondary",13.4900,39.4700,340,170,170,25,19),
    ("ET-SN-001","Hawassa Community School","ET-SN","Sidama Zone","Hawassa","Community","Primary",7.0500,38.4800,560,280,280,48,26),
    ("ET-SN-002","Arba Minch Vocational","ET-SN","Gamo Zone","Arba Minch","Vocational","Secondary",6.0300,37.5500,180,95,85,15,14),
]
sync_dates = [
    datetime.now(timezone.utc).date() - timedelta(days=1),
    datetime.now(timezone.utc).date() - timedelta(days=2),
    datetime.now(timezone.utc).date() - timedelta(days=1),
    datetime.now(timezone.utc).date() - timedelta(days=3),
    datetime.now(timezone.utc).date() - timedelta(days=8),
    datetime.now(timezone.utc).date() - timedelta(days=1),
    datetime.now(timezone.utc).date() - timedelta(days=10),
    datetime.now(timezone.utc).date() - timedelta(days=2),
    datetime.now(timezone.utc).date() - timedelta(days=1),
    datetime.now(timezone.utc).date() - timedelta(days=16),
]
for i, s in enumerate(schools_data):
    cur.execute("""
        INSERT INTO mart.dim_school
            (school_id, school_name, zone, city, school_type,
             education_level, latitude, longitude, total_students,
             total_male, total_female, total_sne, total_teachers,
             last_sync_date, sync_frequency_days, is_active)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (school_id) DO UPDATE SET
            last_sync_date = EXCLUDED.last_sync_date,
            total_students = EXCLUDED.total_students
    """, (s[0],s[1],s[3],s[4],s[5],s[6],s[7],s[8],
          s[9],s[10],s[11],s[12],s[13],sync_dates[i],1,True))
    cur.execute("""
        UPDATE mart.dim_school
        SET geo_id = (
            SELECT geo_id FROM mart.dim_geo_node
            WHERE node_name = %s AND level_number = 3
        )
        WHERE school_id = %s
    """, (s[3], s[0]))
conn.commit()
print("Schools done")

# ------------------------------------------------------------
# CONTENT
# ------------------------------------------------------------
print("Inserting content...")
content_data = [
    ("CONT001","Mathematics Grade 1 Basics","SUB001","PROV001","CT002","LANG001","GR01"),
    ("CONT002","English Reading Comprehension","SUB002","PROV002","CT004","LANG001","GR03"),
    ("CONT003","Amharic Grammar Exercises","SUB003","PROV001","CT006","LANG002","GR02"),
    ("CONT004","General Science Experiments","SUB004","PROV003","CT005","LANG001","GR05"),
    ("CONT005","Biology Cell Structure","SUB005","PROV003","CT005","LANG001","GR09"),
    ("CONT006","Chemistry Periodic Table","SUB006","PROV001","CT004","LANG001","GR10"),
    ("CONT007","Physics Motion Game","SUB007","PROV002","CT003","LANG001","GR11"),
    ("CONT008","Mathematics Arithmetic Game","SUB001","PROV005","CT003","LANG001","GR04"),
    ("CONT009","English Vocabulary Quiz","SUB002","PROV005","CT002","LANG001","GR06"),
    ("CONT010","Social Studies Ethiopia","SUB008","PROV001","CT004","LANG002","GR07"),
    ("CONT011","History Ancient Civilizations","SUB009","PROV002","CT004","LANG001","GR08"),
    ("CONT012","Geography Maps and Regions","SUB010","PROV001","CT005","LANG001","GR07"),
    ("CONT013","ICT Computing Basics","SUB011","PROV002","CT006","LANG001","GR08"),
    ("CONT014","Mathematics Grade 5 Fractions","SUB001","PROV001","CT002","LANG001","GR05"),
    ("CONT015","Science Lab Simulations","SUB004","PROV003","CT005","LANG001","GR06"),
    ("CONT016","Oromo Language Reading","SUB003","PROV001","CT004","LANG003","GR03"),
    ("CONT017","Mathematics Problem Solving","SUB001","PROV002","CT006","LANG001","GR09"),
    ("CONT018","English Grammar Video","SUB002","PROV004","CT001","LANG001","GR04"),
    ("CONT019","Biology Ecosystem Game","SUB005","PROV005","CT003","LANG001","GR10"),
    ("CONT020","Chemistry Reactions Quiz","SUB006","PROV005","CT002","LANG001","GR11"),
]
for c in content_data:
    cur.execute("""
        INSERT INTO mart.dim_content
            (content_id, content_name, subject_id, provider_id,
             content_type_id, language_id, grade_id, is_offline, is_active)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (content_id) DO NOTHING
    """, (c[0],c[1],c[2],c[3],c[4],c[5],c[6],True,True))
conn.commit()
print("Content done")

# ------------------------------------------------------------
# STUDENTS
# ------------------------------------------------------------
print("Inserting students...")
students = []
seq = 1
sne_types = ["Visual impairment","Hearing impairment","Cognitive disability",
             "Physical disability","Dyslexia"]
grades = ["GR01","GR02","GR03","GR04","GR05","GR06","GR07","GR08","GR09","GR10"]

for school in schools_data:
    school_id = school[0]
    num = min(school[9], 55)
    for i in range(num):
        student_id = school_id + "-2025-" + str(seq).zfill(6)
        gender = random.choice(["M","M","F","F","M"])
        grade_id = random.choice(grades)
        has_sne = random.random() < 0.10
        sne_type = random.choice(sne_types) if has_sne else None
        reg_date = datetime.now(timezone.utc).date() - timedelta(days=random.randint(30,365))
        cur.execute("""
            INSERT INTO mart.dim_student
                (student_id, school_id, gender, grade_id,
                 has_special_needs, special_need_type, registration_date, is_active)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (student_id) DO NOTHING
        """, (student_id, school_id, gender, grade_id, has_sne, sne_type, reg_date, True))
        students.append((student_id, school_id, grade_id, gender))
        seq += 1
conn.commit()
print("Students done -- " + str(len(students)) + " total")

# ------------------------------------------------------------
# DEVICES
# ------------------------------------------------------------
print("Inserting devices...")
devices_by_school = {}
dev_seq = 1
for school in schools_data:
    school_id = school[0]
    devices_by_school[school_id] = []
    for i in range(random.randint(10, 20)):
        device_id = "DEV-" + school_id + "-" + str(dev_seq).zfill(6)
        dtype = random.choice(["tablet","tablet","pc","pc","laptop"])
        os = random.choice(["Android","Android","Windows","Ubuntu","ChromeOS"])
        cur.execute("""
            INSERT INTO mart.dim_device
                (device_id, school_id, device_type, os, device_status, is_active)
            VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (device_id) DO NOTHING
        """, (device_id, school_id, dtype, os, "Active", True))
        devices_by_school[school_id].append(device_id)
        dev_seq += 1
conn.commit()
print("Devices done")

# AI USERS -- 30 percent of all students
ai_users = set(s[0] for s in random.sample(students, int(len(students) * 0.30)))
print("AI users: " + str(len(ai_users)))

all_platforms = ["PLT_OA","PLT_CS","PLT_GAME","PLT_H5P","PLT_PHET","PLT_SCORM"]

# ------------------------------------------------------------
# xAPI STATEMENTS
# Each student session generates:
#   1. session-started (no duration)
#   2. content accessed (with duration)
#   3. assessment attempted (40 percent chance, with duration and score)
#   4. AI queried (30 percent of AI students, with duration)
#   5. session-ended (always, with total session duration)
# ------------------------------------------------------------
print("Generating xAPI statements...")
stmt_count = 0

for student_id, school_id, grade_id, gender in students:
    devs = devices_by_school.get(school_id, ["DEV-UNKNOWN"])
    device_id = random.choice(devs)
    server_id = "SRV-" + school_id + "-001"
    num_days = random.randint(5, 50)

    for _ in range(num_days):
        base = rand_date(90, 0)
        if base.weekday() >= 5 and random.random() > 0.2:
            continue
        session_date = school_hour(base)
        platform = random.choice(all_platforms)
        is_offline = random.random() < 0.60
        content = random.choice(content_data)
        content_id = content[0]
        subject_id = content[2]
        session_dur = random.randint(15, 90)
        session_uuid = str(uuid.uuid4())

        # Session started
        verb_s = "https://camara.org/xapi/verbs/session-started"
        fp_s = fp(student_id, verb_s, content_id, session_date.isoformat(), school_id)
        cur.execute("SELECT 1 FROM raw.xapi_statements WHERE event_fingerprint=%s", (fp_s,))
        if not cur.fetchone():
            camara_ctx = {"school_id":school_id,"device_id":device_id,
                         "platform_id":platform,"is_offline":str(is_offline).lower(),
                         "server_id":server_id,"tracking_depth":"full",
                         "session_id":session_uuid}
            cur.execute("""
                INSERT INTO raw.xapi_statements
                    (statement_id,server_id,school_id,actor,verb,
                     object,result,context,timestamp,event_fingerprint)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (str(uuid.uuid4()), server_id, school_id,
                  json.dumps({"objectType":"Agent","account":{"name":student_id,
                              "homePage":"https://camara.org"}}),
                  json.dumps({"id":verb_s}),
                  json.dumps({"id":"https://camara.org/xapi/activities/session/"+session_uuid}),
                  None,
                  json.dumps({"extensions":{"https://camara.org/xapi/context":camara_ctx}}),
                  session_date, fp_s))
            stmt_count += 1
        # Content accessed
        verb_c = "http://adlnet.gov/expapi/verbs/experienced"
        content_time = session_date + timedelta(minutes=random.randint(2,10))
        fp_c = fp(student_id, verb_c, content_id, content_time.isoformat(), school_id)
        cur.execute("SELECT 1 FROM raw.xapi_statements WHERE event_fingerprint=%s", (fp_c,))
        if not cur.fetchone():
            dur = random.randint(5,45)
            completed = random.random() < 0.65
            result_c = {"duration":"PT"+str(dur)+"M",
                       "completion":str(completed).lower()}
            camara_ctx = {"school_id":school_id,"device_id":device_id,
                         "platform_id":platform,"is_offline":str(is_offline).lower(),
                         "server_id":server_id,"tracking_depth":"full"}
            cur.execute("""
                INSERT INTO raw.xapi_statements
                    (statement_id,server_id,school_id,actor,verb,
                     object,result,context,timestamp,event_fingerprint)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (str(uuid.uuid4()), server_id, school_id,
                  json.dumps({"objectType":"Agent","account":{"name":student_id,
                              "homePage":"https://camara.org"}}),
                  json.dumps({"id":verb_c}),
                  json.dumps({"id":"https://camara.org/content/"+content_id,
                              "definition":{"name":{"en-US":content[1]}}}),
                  json.dumps(result_c),
                  json.dumps({"extensions":{"https://camara.org/xapi/context":camara_ctx}}),
                  content_time, fp_c))
            stmt_count += 1

        # Assessment -- 40 percent chance
        if random.random() < 0.40:
            verb_a = "http://adlnet.gov/expapi/verbs/attempted"
            assess_time = content_time + timedelta(minutes=random.randint(5,20))
            score = random.randint(40,95)
            fp_a = fp(student_id, verb_a, content_id, assess_time.isoformat(), school_id)
            cur.execute("SELECT 1 FROM raw.xapi_statements WHERE event_fingerprint=%s",
                       (fp_a,))
            if not cur.fetchone():
                result_a = {"score":{"raw":score,"min":0,"max":100,
                                    "scaled":round(score/100,4)},
                           "success":str(score>=50).lower(),
                           "duration":"PT"+str(random.randint(5,30))+"M"}
                camara_ctx = {"school_id":school_id,"device_id":device_id,
                             "platform_id":platform,"is_offline":str(is_offline).lower(),
                             "server_id":server_id,"tracking_depth":"full",
                             "subject_id":subject_id,"attempt_number":"1"}
                cur.execute("""
                    INSERT INTO raw.xapi_statements
                        (statement_id,server_id,school_id,actor,verb,
                         object,result,context,timestamp,event_fingerprint)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (str(uuid.uuid4()), server_id, school_id,
                      json.dumps({"objectType":"Agent","account":{"name":student_id,
                                  "homePage":"https://camara.org"}}),
                      json.dumps({"id":verb_a}),
                      json.dumps({"id":"https://camara.org/assessment/"+content_id,
                                  "definition":{"name":{"en-US":content[1]+" Quiz"}}}),
                      json.dumps(result_a),
                      json.dumps({"extensions":{"https://camara.org/xapi/context":camara_ctx}}),
                      assess_time, fp_a))
                stmt_count += 1

        # AI query -- 30 percent of students
        if student_id in ai_users and random.random() < 0.50:
            verb_ai = "https://camara.org/xapi/verbs/ai-queried"
            ai_time = content_time + timedelta(minutes=random.randint(1,10))
            fp_ai = fp(student_id, verb_ai, "AI001", ai_time.isoformat(), school_id)
            cur.execute("SELECT 1 FROM raw.xapi_statements WHERE event_fingerprint=%s",
                       (fp_ai,))
            if not cur.fetchone():
                qtype = random.choice(["Clarification","Problem-solving","Guidance",
                                      "Translation","Practice"])
                result_ai = {"duration":"PT"+str(random.randint(1,8))+"M"}
                camara_ctx = {"school_id":school_id,"device_id":device_id,
                             "platform_id":platform,"is_offline":str(is_offline).lower(),
                             "server_id":server_id,"tracking_depth":"full",
                             "subject_id":subject_id,"query_type":qtype}
                cur.execute("""
                    INSERT INTO raw.xapi_statements
                        (statement_id,server_id,school_id,actor,verb,
                         object,result,context,timestamp,event_fingerprint)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (str(uuid.uuid4()), server_id, school_id,
                      json.dumps({"objectType":"Agent","account":{"name":student_id,
                                  "homePage":"https://camara.org"}}),
                      json.dumps({"id":verb_ai}),
                      json.dumps({"id":"https://camara.org/ai/AI001"}),
                      json.dumps(result_ai),
                      json.dumps({"extensions":{"https://camara.org/xapi/context":camara_ctx}}),
                      ai_time, fp_ai))
                stmt_count += 1

        # Session ended -- always generated with total session duration
        # Duration is the total session length from session_date
        # This is critical for total_learning_hours to be populated
        verb_se = "https://camara.org/xapi/verbs/session-ended"
        session_end_time = session_date + timedelta(minutes=session_dur)
        fp_se = fp(student_id, verb_se, content_id,
                  session_end_time.isoformat(), school_id)
        cur.execute("SELECT 1 FROM raw.xapi_statements WHERE event_fingerprint=%s",
                   (fp_se,))
        if not cur.fetchone():
            camara_ctx_se = {"school_id":school_id,"device_id":device_id,
                            "platform_id":platform,"is_offline":str(is_offline).lower(),
                            "server_id":server_id,"tracking_depth":"full",
                            "session_id":session_uuid}
            cur.execute("""
                INSERT INTO raw.xapi_statements
                    (statement_id,server_id,school_id,actor,verb,
                     object,result,context,timestamp,event_fingerprint)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (str(uuid.uuid4()), server_id, school_id,
                  json.dumps({"objectType":"Agent","account":{"name":student_id,
                              "homePage":"https://camara.org"}}),
                  json.dumps({"id":verb_se}),
                  json.dumps({"id":"https://camara.org/xapi/activities/session/"+session_uuid}),
                  json.dumps({"duration":"PT"+str(session_dur)+"M"}),
                  json.dumps({"extensions":{"https://camara.org/xapi/context":camara_ctx_se}}),
                  session_end_time, fp_se))
            stmt_count += 1


        # Resource events -- app, site, or book usage during this session
        # Matches the pattern emitted by edge/device_tracker.py on real
        # devices -- opened/closed pairs with duration on the closed event
        resource_pool = [
            ("app", "app/vscode", "VS Code"),
            ("app", "app/notepad", "Notepad"),
            ("site", "site/wikipedia_org", "Wikipedia"),
            ("site", "site/khan_academy", "Khan Academy"),
            ("book", "book/grade_reader", "Grade Reader"),
        ]
        if random.random() < 0.70:
            res_type, res_id, res_name = random.choice(resource_pool)
            res_open_time = content_time + timedelta(minutes=random.randint(1, 5))
            res_dur = random.randint(2, 20)
            res_close_time = res_open_time + timedelta(minutes=res_dur)

            verb_ro = "https://camara.org/xapi/verbs/" + res_type + "-" + ("visited" if res_type == "site" else "opened")
            fp_ro = fp(student_id, verb_ro, res_id, res_open_time.isoformat(), school_id)
            cur.execute("SELECT 1 FROM raw.xapi_statements WHERE event_fingerprint=%s", (fp_ro,))
            if not cur.fetchone():
                camara_ctx_ro = {"school_id":school_id,"device_id":device_id,
                                "platform_id":platform,"is_offline":str(is_offline).lower(),
                                "server_id":server_id,"tracking_depth":"full",
                                "session_id":session_uuid}
                cur.execute("""
                    INSERT INTO raw.xapi_statements
                        (statement_id,server_id,school_id,actor,verb,
                         object,result,context,timestamp,event_fingerprint)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (str(uuid.uuid4()), server_id, school_id,
                      json.dumps({"objectType":"Agent","account":{"name":student_id,
                                  "homePage":"https://camara.org"}}),
                      json.dumps({"id":verb_ro}),
                      json.dumps({"id":"https://camara.org/xapi/activities/resource/"+res_id,
                                  "definition":{"name":{"en-US":res_name}}}),
                      None,
                      json.dumps({"extensions":{"https://camara.org/xapi/context":camara_ctx_ro}}),
                      res_open_time, fp_ro))
                stmt_count += 1

            verb_rc = "https://camara.org/xapi/verbs/" + res_type + "-" + ("left" if res_type == "site" else "closed")
            fp_rc = fp(student_id, verb_rc, res_id, res_close_time.isoformat(), school_id)
            cur.execute("SELECT 1 FROM raw.xapi_statements WHERE event_fingerprint=%s", (fp_rc,))
            if not cur.fetchone():
                camara_ctx_rc = {"school_id":school_id,"device_id":device_id,
                                "platform_id":platform,"is_offline":str(is_offline).lower(),
                                "server_id":server_id,"tracking_depth":"full",
                                "session_id":session_uuid}
                cur.execute("""
                    INSERT INTO raw.xapi_statements
                        (statement_id,server_id,school_id,actor,verb,
                         object,result,context,timestamp,event_fingerprint)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (str(uuid.uuid4()), server_id, school_id,
                      json.dumps({"objectType":"Agent","account":{"name":student_id,
                                  "homePage":"https://camara.org"}}),
                      json.dumps({"id":verb_rc}),
                      json.dumps({"id":"https://camara.org/xapi/activities/resource/"+res_id,
                                  "definition":{"name":{"en-US":res_name}}}),
                      json.dumps({"duration":"PT"+str(res_dur)+"M"}),
                      json.dumps({"extensions":{"https://camara.org/xapi/context":camara_ctx_rc}}),
                      res_close_time, fp_rc))
                stmt_count += 1

        # Idle event -- 25 percent chance of one idle period per session
        if random.random() < 0.25:
            idle_start_time = session_date + timedelta(minutes=random.randint(5, session_dur - 2) if session_dur > 7 else 3)
            idle_dur_seconds = random.randint(30, 300)
            idle_end_time = idle_start_time + timedelta(seconds=idle_dur_seconds)
            session_obj_id = "https://camara.org/xapi/activities/session/" + str(uuid.uuid4())

            verb_is = "https://camara.org/xapi/verbs/idle-started"
            fp_is = fp(student_id, verb_is, session_obj_id, idle_start_time.isoformat(), school_id)
            cur.execute("SELECT 1 FROM raw.xapi_statements WHERE event_fingerprint=%s", (fp_is,))
            if not cur.fetchone():
                camara_ctx_is = {"school_id":school_id,"device_id":device_id,
                                "platform_id":platform,"is_offline":str(is_offline).lower(),
                                "server_id":server_id,"tracking_depth":"full",
                                "session_id":session_uuid}
                cur.execute("""
                    INSERT INTO raw.xapi_statements
                        (statement_id,server_id,school_id,actor,verb,
                         object,result,context,timestamp,event_fingerprint)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (str(uuid.uuid4()), server_id, school_id,
                      json.dumps({"objectType":"Agent","account":{"name":student_id,
                                  "homePage":"https://camara.org"}}),
                      json.dumps({"id":verb_is}),
                      json.dumps({"id":session_obj_id}),
                      None,
                      json.dumps({"extensions":{"https://camara.org/xapi/context":camara_ctx_is}}),
                      idle_start_time, fp_is))
                stmt_count += 1

            verb_ie = "https://camara.org/xapi/verbs/idle-ended"
            fp_ie = fp(student_id, verb_ie, session_obj_id, idle_end_time.isoformat(), school_id)
            cur.execute("SELECT 1 FROM raw.xapi_statements WHERE event_fingerprint=%s", (fp_ie,))
            if not cur.fetchone():
                camara_ctx_ie = {"school_id":school_id,"device_id":device_id,
                                "platform_id":platform,"is_offline":str(is_offline).lower(),
                                "server_id":server_id,"tracking_depth":"full",
                                "session_id":session_uuid}
                cur.execute("""
                    INSERT INTO raw.xapi_statements
                        (statement_id,server_id,school_id,actor,verb,
                         object,result,context,timestamp,event_fingerprint)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (str(uuid.uuid4()), server_id, school_id,
                      json.dumps({"objectType":"Agent","account":{"name":student_id,
                                  "homePage":"https://camara.org"}}),
                      json.dumps({"id":verb_ie}),
                      json.dumps({"id":session_obj_id}),
                      json.dumps({"duration":"PT"+str(idle_dur_seconds)+"S"}),
                      json.dumps({"extensions":{"https://camara.org/xapi/context":camara_ctx_ie}}),
                      idle_end_time, fp_ie))
                stmt_count += 1

    # Commit per student to avoid timeout
    conn.commit()

print("xAPI statements done -- " + str(stmt_count) + " total")

# ------------------------------------------------------------
# SYNC LOG
# Generates realistic sync history for each school
# Used by mart_completeness to calculate sync health
# Includes entries for today so completeness shows data reporting today
# ------------------------------------------------------------
print("Inserting sync log entries...")
for school in schools_data:
    school_id = school[0]
    server_id = "SRV-" + school_id + "-001"
    # Historical sync entries
    for i in range(random.randint(5, 12)):
        sync_time = rand_date(90, 1)
        cur.execute("""
            INSERT INTO ops.sync_log
                (sync_id, server_id, school_id, request_id,
                 statements_received, statements_inserted,
                 statements_rejected, statements_duplicate,
                 import_source, status, synced_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (sync_id) DO NOTHING
        """, ("SYNC-"+str(uuid.uuid4()), server_id, school_id,
              "REQ-"+sync_time.strftime("%Y%m%d")+"-"+
              school_id.replace("-","")+"-"+str(random.randint(1000,9999)),
              random.randint(50,500), random.randint(40,490),
              random.randint(0,5), random.randint(0,20),
              "sync_agent", "ok", sync_time))
    # Today sync entry for schools that have recent sync dates
    # This ensures mart_completeness shows schools reporting today
    sync_date = sync_dates[schools_data.index(school)]
    days_since_sync = (datetime.now(timezone.utc).date() - sync_date).days
    if days_since_sync <= 1:
        today_sync_time = datetime.now(timezone.utc).replace(
            hour=random.randint(6,22),
            minute=random.randint(0,59),
            second=0,
            microsecond=0
        )
        cur.execute("""
            INSERT INTO ops.sync_log
                (sync_id, server_id, school_id, request_id,
                 statements_received, statements_inserted,
                 statements_rejected, statements_duplicate,
                 import_source, status, synced_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (sync_id) DO NOTHING
        """, ("SYNC-"+str(uuid.uuid4()), server_id, school_id,
              "REQ-"+today_sync_time.strftime("%Y%m%d")+"-"+
              school_id.replace("-","")+"-"+str(random.randint(1000,9999)),
              random.randint(50,500), random.randint(40,490),
              random.randint(0,5), random.randint(0,20),
              "sync_agent", "ok", today_sync_time))
conn.commit()
print("Sync log done")

cur.close()
conn.close()

print("")
print("Sample data generation complete")
print("Total xAPI statements: " + str(stmt_count))
print("Total students: " + str(len(students)))
print("")
print("Now run: dbt run --project-dir cdlaid_dbt")
