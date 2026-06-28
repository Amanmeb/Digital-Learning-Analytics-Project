# CDLAID School Server Installer
# Replaces install_school.sh -- no Moodle, login_app instead
# Runs identically on Windows (dev/test) and Ubuntu (real deployment)
# Run as: python install_school.py
import os
import platform
import subprocess
import sys


def print_header(text):
    # Prints a section header
    print("")
    print(text)
    print("=" * len(text))
    print("")


def ask(prompt, default=None):
    # Asks a question, returns default if user presses enter
    if default:
        full_prompt = prompt + " [" + str(default) + "]: "
    else:
        full_prompt = prompt + ": "
    answer = input(full_prompt).strip()
    if not answer and default:
        return default
    return answer


def ask_choice(prompt, options):
    # Asks the user to choose from a numbered list of options
    print(prompt)
    for index, option in enumerate(options, start=1):
        print("  " + str(index) + " -- " + option)
    while True:
        choice = input("Enter choice: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("Invalid choice, try again")


def is_linux():
    # Returns True if running on Linux, False otherwise
    return platform.system() == "Linux"


def fetch_geo_picker(central_host, central_port, central_password):
    # Attempts to fetch the geo hierarchy from the central database
    # Returns a list of dicts, or None if unreachable
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=central_host,
            port=central_port,
            user="cdlaid_user",
            password=central_password,
            dbname="cdlaid_analytics",
            connect_timeout=5,
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT geo_id, level_number, node_name, country_code "
            "FROM mart.dim_geo_node ORDER BY level_number, node_name"
        )
        rows = cur.fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({
                "geo_id": row[0],
                "level_number": row[1],
                "node_name": row[2],
                "country_code": row[3],
            })
        return result
    except Exception:
        return None


def collect_school_identity(central_host, central_port, central_password):
    # Collects country/region/woreda and school identity
    # Tries the central picker first, falls back to manual entry
    print_header("Phase 1 -- School Identity")

    geo_nodes = fetch_geo_picker(central_host, central_port, central_password)

    country_code = "ET"
    region_name = ""
    woreda_name = ""

    if geo_nodes:
        print("Connected to central server -- showing available regions")
        regions = [n for n in geo_nodes if n["level_number"] == 2]
        for index, region in enumerate(regions, start=1):
            print("  " + str(index) + " -- " + region["node_name"])
        region_choice = ask("Enter region number, or type a new region name")
        if region_choice.isdigit() and 1 <= int(region_choice) <= len(regions):
            chosen = regions[int(region_choice) - 1]
            region_name = chosen["node_name"]
            country_code = chosen["country_code"]
        else:
            region_name = region_choice
        woreda_name = ask("Woreda or district name")
    else:
        print("Central server not reachable -- using manual entry")
        print("This will be reconciled with the central geo hierarchy")
        print("the next time this school syncs successfully")
        country_code = ask("Country code", "ET")
        region_name = ask("Region name")
        woreda_name = ask("Woreda or district name")

    school_name = ask("School name")
    school_id = ask("School ID (format COUNTRY-REGIONCODE-NUMBER, e.g. ET-AA-001)")

    return {
        "country_code": country_code,
        "region_name": region_name,
        "woreda_name": woreda_name,
        "school_name": school_name,
        "school_id": school_id,
    }


def collect_connection_method():
    # Collects hotspot/LAN/both connection method, matching the
    # original install_school.sh logic
    print_header("Phase 2 -- Connection Method")

    choice = ask_choice(
        "Choose connection method:",
        [
            "Hotspot only (students connect to school WiFi hotspot)",
            "LAN/ethernet only (school has existing wired network)",
            "Both hotspot and LAN simultaneously",
        ],
    )

    if choice.startswith("Hotspot"):
        connection_method = "hotspot"
    elif choice.startswith("LAN"):
        connection_method = "lan"
    else:
        connection_method = "both"

    lan_ip = ""
    if connection_method in ("lan", "both"):
        lan_ip = ask("Enter LAN IP address for this server (e.g. 192.168.1.100)")
        if not lan_ip and connection_method == "lan":
            print("No LAN IP entered -- falling back to hotspot only")
            connection_method = "hotspot"

    return {"connection_method": connection_method, "lan_ip": lan_ip}


def collect_school_year():
    # Collects school year start and end month
    print_header("Phase 3 -- School Year")
    start_month = ask("School year start month, 1 to 12", "9")
    end_month = ask("School year end month, 1 to 12", "7")
    return {"school_year_start_month": start_month, "school_year_end_month": end_month}


def collect_curriculum_defaults():
    # Confirms Ethiopian curriculum defaults, allows override
    print_header("Phase 4 -- Curriculum Defaults")
    print("Default grades: Primary 1-8, Secondary 9-12 (Ethiopian standard)")
    print("Default subjects: Mathematics, English, Amharic, Science,")
    print("Social Studies, ICT, Art, Physical Education")
    use_defaults = ask("Use these defaults? (yes/no)", "yes")
    if use_defaults.lower() == "yes":
        return {"curriculum": "ethiopian_default"}
    custom_grades = ask("Enter custom grade list, comma separated")
    custom_subjects = ask("Enter custom subject list, comma separated")
    return {
        "curriculum": "custom",
        "custom_grades": custom_grades,
        "custom_subjects": custom_subjects,
    }


def collect_images():
    # Tells the admin exactly what image files are needed, where
    print_header("Phase 5 -- Images")
    print("School logo (optional, can be added later):")
    print("  Folder:   login_app/assets/")
    print("  Filename: school_logo.png")
    print("  Format:   PNG, transparent background")
    print("  Size:     512x512 pixels")
    print("")
    has_logo = ask("Have you placed school_logo.png in that folder now? (yes/no)", "no")
    return {"school_logo_provided": has_logo.lower() == "yes"}


def collect_secrets():
    # Collects all passwords and secrets -- admin types every one
    print_header("Phase 6 -- Passwords and Secrets")
    db_password = ask("Database password for this school server")
    superset_password = ask("Superset admin password")
    api_key = ask("API key shared with central server")
    device_receiver_key = ask("Device receiver key")
    admin_api_key = ask("Admin API key for registration endpoints")
    return {
        "db_password": db_password,
        "superset_password": superset_password,
        "api_key": api_key,
        "device_receiver_key": device_receiver_key,
        "admin_api_key": admin_api_key,
    }


def collect_ports():
    # Collects port overrides, shows defaults
    print_header("Phase 7 -- Ports")
    postgres_port = ask("PostgreSQL port", "5433")
    superset_port = ask("Superset port", "8089")
    login_port = ask("Login app port", "3000")
    device_receiver_port = ask("Device receiver port", "8000")
    return {
        "postgres_port": postgres_port,
        "superset_port": superset_port,
        "login_port": login_port,
        "device_receiver_port": device_receiver_port,
    }


def print_summary(config):
    # Prints the full configuration for final confirmation
    print_header("Phase 8 -- Summary")
    for key in sorted(config.keys()):
        if "password" in key or "key" in key:
            print("  " + key + ": ********")
        else:
            print("  " + key + ": " + str(config[key]))
    print("")
    confirm = ask("Proceed with this configuration? (yes/no)", "yes")
    return confirm.lower() == "yes"


def write_env_file(config):
    # Writes .env.school with all collected configuration
    lines = []
    lines.append("SCHOOL_ID=" + config["school_id"])
    lines.append("SCHOOL_NAME=" + config["school_name"])
    lines.append("COUNTRY_CODE=" + config["country_code"])
    lines.append("REGION_NAME=" + config["region_name"])
    lines.append("WOREDA_NAME=" + config["woreda_name"])
    lines.append("SERVER_ID=SRV-" + config["school_id"] + "-001")
    lines.append("CONNECTION_METHOD=" + config["connection_method"])
    lines.append("LAN_IP=" + config["lan_ip"])
    lines.append("SCHOOL_YEAR_START_MONTH=" + config["school_year_start_month"])
    lines.append("SCHOOL_YEAR_END_MONTH=" + config["school_year_end_month"])
    lines.append("POSTGRES_PASSWORD=" + config["db_password"])
    lines.append("SUPERSET_ADMIN_PASSWORD=" + config["superset_password"])
    lines.append("SCHOOL_API_KEY=" + config["api_key"])
    lines.append("DEVICE_RECEIVER_KEY=" + config["device_receiver_key"])
    lines.append("ADMIN_API_KEY=" + config["admin_api_key"])
    lines.append("QUEUE_DB_PATH=/opt/cdlaid/edge/queue.db")

    with open(".env.school", "w") as env_file:
        env_file.write("\n".join(lines) + "\n")

    print("Environment file .env.school written")


def run_docker_compose_up():
    # Starts the school stack -- postgres, superset, device_receiver,
    # login_app -- no Moodle, no MySQL
    print_header("Phase 9 -- Starting Services")
    subprocess.run(
        ["docker", "compose", "--env-file", ".env.school", "-f",
         "docker-compose.school.yml", "up", "-d", "--build"],
        check=True,
    )
    print("Waiting for services to become healthy")
    import time
    time.sleep(30)


def run_dbt_seed_and_run():
    # Runs dbt seed and dbt run against the school target
    print_header("Phase 10 -- Database Setup")
    subprocess.run(
        ["dbt", "seed", "--project-dir", "cdlaid_dbt", "--profiles-dir", "cdlaid_dbt",
         "--profile", "cdlaid_dbt", "--target", "school"],
        check=True,
    )
    subprocess.run(
        ["dbt", "run", "--project-dir", "cdlaid_dbt", "--profiles-dir", "cdlaid_dbt",
         "--profile", "cdlaid_dbt", "--target", "school"],
        check=True,
    )


def setup_hotspot_linux(school_id, connection_method):
    # Configures a WiFi hotspot using nmcli -- Linux only
    if not is_linux():
        print("Hotspot setup skipped -- not running on Linux")
        return False
    if connection_method not in ("hotspot", "both"):
        return False

    print_header("Hotspot Setup")
    check_nmcli = subprocess.run(["which", "nmcli"], capture_output=True)
    if check_nmcli.returncode != 0:
        print("nmcli not found -- skipping hotspot setup")
        print("Install with: sudo apt-get install network-manager")
        return False

    hotspot_name = "Camara-" + school_id
    hotspot_password = "camara" + school_id.replace("-", "")

    device_check = subprocess.run(
        ["nmcli", "device", "status"], capture_output=True, text=True
    )
    wifi_adapter = None
    for line in device_check.stdout.splitlines():
        if "wifi" in line:
            wifi_adapter = line.split()[0]
            break

    if not wifi_adapter:
        print("No WiFi adapter found -- skipping hotspot setup")
        return False

    subprocess.run(["nmcli", "connection", "delete", hotspot_name], capture_output=True)
    subprocess.run([
        "nmcli", "connection", "add", "type", "wifi", "ifname", wifi_adapter,
        "con-name", hotspot_name, "autoconnect", "yes", "ssid", hotspot_name,
        "--", "wifi.mode", "ap", "wifi-sec.key-mgmt", "wpa-psk",
        "wifi-sec.psk", hotspot_password, "ipv4.method", "shared",
        "ipv4.addresses", "10.42.0.1/24",
    ], check=True)
    subprocess.run(["nmcli", "connection", "up", hotspot_name], check=True)

    print("Hotspot configured:")
    print("  Network name: " + hotspot_name)
    print("  Password:     " + hotspot_password)
    print("  Server IP:    10.42.0.1")
    return True


def setup_systemd_services_linux():
    # Installs the sync agent and sync monitor as systemd services
    # Linux only -- skipped on Windows
    if not is_linux():
        print("Systemd service setup skipped -- not running on Linux")
        return

    print_header("Systemd Services")
    sync_agent_unit = (
        "[Unit]\n"
        "Description=CDLAID Sync Agent\n"
        "After=network.target docker.service\n"
        "Wants=network.target\n\n"
        "[Service]\n"
        "Type=simple\n"
        "User=ubuntu\n"
        "WorkingDirectory=/opt/cdlaid\n"
        "EnvironmentFile=/opt/cdlaid/.env.school\n"
        "ExecStart=/usr/bin/python3 -m edge.sync_agent\n"
        "Restart=always\n"
        "RestartSec=30\n\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n"
    )
    sync_monitor_unit = (
        "[Unit]\n"
        "Description=CDLAID School Status Monitor\n"
        "After=network.target\n\n"
        "[Service]\n"
        "Type=simple\n"
        "User=ubuntu\n"
        "WorkingDirectory=/opt/cdlaid\n"
        "EnvironmentFile=/opt/cdlaid/.env.school\n"
        "ExecStart=/usr/bin/python3 -m edge.sync_monitor\n"
        "Restart=always\n"
        "RestartSec=10\n\n"
        "[Install]\n"
        "WantedBy=multi-user.target\n"
    )

    with open("/etc/systemd/system/cdlaid-sync-agent.service", "w") as service_file:
        service_file.write(sync_agent_unit)
    with open("/etc/systemd/system/cdlaid-sync-monitor.service", "w") as service_file:
        service_file.write(sync_monitor_unit)

    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", "cdlaid-sync-agent"], check=True)
    subprocess.run(["systemctl", "enable", "cdlaid-sync-monitor"], check=True)
    subprocess.run(["systemctl", "start", "cdlaid-sync-agent"], check=True)
    subprocess.run(["systemctl", "start", "cdlaid-sync-monitor"], check=True)
    print("Sync agent and sync monitor installed and started")


def print_final_summary(config, hotspot_configured):
    # Prints the final URLs and credentials
    print_header("Installation Complete")
    if hotspot_configured:
        login_url = "http://10.42.0.1:" + config["login_port"]
    elif config["lan_ip"]:
        login_url = "http://" + config["lan_ip"] + ":" + config["login_port"]
    else:
        login_url = "http://localhost:" + config["login_port"]

    print("  School:            " + config["school_name"])
    print("  School ID:         " + config["school_id"])
    print("  Connection method: " + config["connection_method"])
    print("  Login app:         " + login_url)
    print("  Superset:          http://localhost:" + config["superset_port"])
    print("")
    print("To change connection method later, edit .env.school and re-run")
    print("this installer.")


def main():
    # Runs the full school server installation flow
    print_header("CDLAID School Server Installer")
    print("Replaces install_school.sh -- no Moodle, login_app instead")

    central_host = ask("Central server host or IP", "localhost")
    central_port = ask("Central server PostgreSQL port", "5432")
    central_password = ask("Central server database password")

    config = {}
    config.update(collect_school_identity(central_host, central_port, central_password))
    config.update(collect_connection_method())
    config.update(collect_school_year())
    config.update(collect_curriculum_defaults())
    config.update(collect_images())
    config.update(collect_secrets())
    config.update(collect_ports())

    if not print_summary(config):
        print("Installation cancelled")
        sys.exit(0)

    write_env_file(config)
    run_docker_compose_up()
    run_dbt_seed_and_run()

    hotspot_configured = setup_hotspot_linux(
        config["school_id"], config["connection_method"]
    )
    setup_systemd_services_linux()

    print_final_summary(config, hotspot_configured)


if __name__ == "__main__":
    main()