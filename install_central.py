# CDLAID Central Server Installer
# Runs identically on Windows (dev/test) and Ubuntu (real deployment)
# Run as: python install_central.py
import os
import subprocess
import sys
import glob


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


def collect_country_scope():
    # Collects which country codes this central server serves
    print_header("Phase 1 -- Country Scope")
    countries_raw = ask(
        "Country codes this central server serves, comma separated", "ET"
    )
    countries = [c.strip().upper() for c in countries_raw.split(",") if c.strip()]
    return {"country_codes": countries}


def collect_geo_level_names(country_codes):
    # Collects level naming for each country's geo hierarchy
    # Ethiopia's real structure is 4 levels below the top: Country,
    # Region, Zone, Woreda -- chartered cities like Addis Ababa use
    # sub-cities in place of a zone. This was previously modeled as
    # only 3 levels (mislabeling zone data as woreda), fixed in
    # migration 013 -- kept consistent here.
    print_header("Phase 2 -- Geo Level Names")
    level_configs = []
    for country_code in country_codes:
        print("Country: " + country_code)
        if country_code == "ET":
            print("Default Ethiopian levels: 1=Country, 2=Region, 3=Zone, 4=Woreda")
            use_default = ask("Use these defaults? (yes/no)", "yes")
            if use_default.lower() == "yes":
                level_configs.append((country_code, 1, "Country"))
                level_configs.append((country_code, 2, "Region"))
                level_configs.append((country_code, 3, "Zone"))
                level_configs.append((country_code, 4, "Woreda"))
                continue
        level_1 = ask("Level 1 name for " + country_code, "Country")
        level_2 = ask("Level 2 name for " + country_code, "Region")
        level_3 = ask("Level 3 name for " + country_code, "Zone")
        level_4 = ask("Level 4 name for " + country_code, "Woreda")
        level_configs.append((country_code, 1, level_1))
        level_configs.append((country_code, 2, level_2))
        level_configs.append((country_code, 3, level_3))
        level_configs.append((country_code, 4, level_4))
    return {"level_configs": level_configs}


def collect_secrets():
    # Collects all passwords and secrets -- admin types every one
    print_header("Phase 3 -- Passwords and Secrets")
    db_password = ask("Database password")
    superset_secret_key = ask("Superset secret key")
    superset_password = ask("Superset admin password")
    superset_email = ask("Superset admin email")
    api_secret_key = ask("API secret key")
    lrs_key = ask("LRS API key")
    lrs_secret = ask("LRS API secret")
    lrs_admin_user = ask("LRS admin username")
    lrs_admin_password = ask("LRS admin password")
    return {
        "db_password": db_password,
        "superset_secret_key": superset_secret_key,
        "superset_password": superset_password,
        "superset_email": superset_email,
        "api_secret_key": api_secret_key,
        "lrs_key": lrs_key,
        "lrs_secret": lrs_secret,
        "lrs_admin_user": lrs_admin_user,
        "lrs_admin_password": lrs_admin_password,
    }


def ask_port(prompt, default):
    # Asks for a port number, re-prompts until a valid integer is given
    while True:
        value = ask(prompt, default)
        if value.isdigit():
            return value
        print("Port must be a number, try again")


def collect_ports():
    # Collects port overrides, shows defaults
    print_header("Phase 4 -- Ports")
    postgres_port = ask_port("PostgreSQL port", "5432")
    superset_port = ask_port("Superset port", "8088")
    api_port = ask_port("API port", "8000")
    lrs_port = ask_port("LRS port", "8080")
    return {
        "postgres_port": postgres_port,
        "superset_port": superset_port,
        "api_port": api_port,
        "lrs_port": lrs_port,
    }


def collect_images():
    # Tells the admin exactly what image files are needed, where
    print_header("Phase 5 -- Images")
    print("Camara logo (reused from pwa/Camara_logo.png if present):")
    print("  Folder:   pwa/")
    print("  Filename: Camara_logo.png")
    print("  Format:   PNG, transparent background")
    print("  Size:     512x512 pixels")
    print("")
    print("Favicon (optional, can be added later):")
    print("  Folder:   login_app/assets/")
    print("  Filename: favicon.png")
    print("  Format:   PNG")
    print("  Size:     256x256 pixels")
    has_camara_logo = os.path.exists("pwa/Camara_logo.png")
    print("")
    if has_camara_logo:
        print("Camara_logo.png found -- will be reused")
    else:
        print("Camara_logo.png not found -- can be added later")
    return {"camara_logo_found": has_camara_logo}


def print_summary(config):
    # Prints the full configuration for final confirmation
    print_header("Phase 6 -- Summary")
    for key in sorted(config.keys()):
        if "password" in key or "key" in key or "secret" in key:
            print("  " + key + ": ********")
        else:
            print("  " + key + ": " + str(config[key]))
    print("")
    confirm = ask("Proceed with this configuration? (yes/no)", "yes")
    return confirm.lower() == "yes"


def write_env_file(config):
    # Writes .env with all collected configuration
    # Refuses to silently overwrite an existing .env -- asks first
    if os.path.exists(".env"):
        print("")
        print("WARNING: .env already exists on this machine")
        overwrite = ask("Overwrite it? (yes/no)", "no")
        if overwrite.lower() != "yes":
            print("Keeping existing .env -- skipping write")
            return False

    lines = []
    lines.append("POSTGRES_PASSWORD=" + config["db_password"])
    lines.append("SUPERSET_SECRET_KEY=" + config["superset_secret_key"])
    lines.append("SUPERSET_ADMIN_PASSWORD=" + config["superset_password"])
    lines.append("SUPERSET_ADMIN_EMAIL=" + config["superset_email"])
    lines.append("API_SECRET_KEY=" + config["api_secret_key"])
    lines.append("LRS_KEY=" + config["lrs_key"])
    lines.append("LRS_SECRET=" + config["lrs_secret"])
    lines.append("LRS_ADMIN_USER=" + config["lrs_admin_user"])
    lines.append("LRS_ADMIN_PASSWORD=" + config["lrs_admin_password"])
    lines.append("ENVIRONMENT=production")
    lines.append("DEMO_MODE=false")
    lines.append("SERVER_ID=")
    lines.append("SCHOOL_ID=")

    with open(".env", "w") as env_file:
        env_file.write("\n".join(lines) + "\n")

    print("Environment file .env written")
    return True


def run_docker_compose_up():
    # Starts the central stack -- postgres, lrs, api, superset
    print_header("Phase 7 -- Starting Services")
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose.central.yml", "up", "-d", "--build"],
        check=True,
    )
    print("Waiting for services to become healthy")
    import time
    time.sleep(30)


def run_migrations():
    # Runs every sql/migrations/*.sql file in numeric order
    print_header("Phase 8 -- Database Migrations")
    migration_files = sorted(glob.glob("sql/migrations/*.sql"))
    for migration_file in migration_files:
        print("Running " + migration_file)
        with open(migration_file, "r") as sql_file:
            sql_content = sql_file.read()
        result = subprocess.run(
            ["docker", "exec", "-i", "-e", "PGPASSWORD=" + os.environ.get(
                "POSTGRES_PASSWORD", "CdlaidDB2025!Strong"),
             "cdlaid_postgres", "psql", "-U", "cdlaid_user", "-d",
             "cdlaid_analytics"],
            input=sql_content,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("Migration may have already been applied, continuing")
            print(result.stderr)


def run_dbt_seed_and_run():
    # Runs dbt seed and dbt run against the central target
    print_header("Phase 9 -- dbt Seed and Run")
    subprocess.run(["dbt", "seed", "--project-dir", "cdlaid_dbt"], check=True)
    subprocess.run(["dbt", "run", "--project-dir", "cdlaid_dbt"], check=True)


def write_geo_level_config(level_configs):
    # Writes the collected geo level names into dim_geo_level_config
    # Uses psql variables instead of string concatenation to avoid
    # SQL injection from user-entered country/level names
    print_header("Phase 10 -- Geo Level Configuration")
    for country_code, level_number, level_name in level_configs:
        sql = (
            "INSERT INTO mart.dim_geo_level_config "
            "(country_code, level_number, level_name) VALUES "
            "(:'country_code', :level_number, :'level_name') "
            "ON CONFLICT DO NOTHING;"
        )
        subprocess.run(
            ["docker", "exec", "-i", "-e", "PGPASSWORD=" + os.environ.get(
                "POSTGRES_PASSWORD", "CdlaidDB2025!Strong"),
             "cdlaid_postgres", "psql", "-U", "cdlaid_user", "-d",
             "cdlaid_analytics",
             "-v", "country_code=" + country_code,
             "-v", "level_number=" + str(level_number),
             "-v", "level_name=" + level_name],
            input=sql,
            capture_output=True,
            text=True,
        )
    print("Geo level configuration written")


def print_final_summary(config):
    # Prints the final URLs and credentials
    print_header("Installation Complete")
    print("  Superset: http://localhost:" + config["superset_port"])
    print("  API:      http://localhost:" + config["api_port"])
    print("  LRS:      http://localhost:" + config["lrs_port"])
    print("")
    print("Superset admin account is created automatically on first")
    print("startup using the admin password and email provided above.")


def main():
    # Runs the full central server installation flow
    print_header("CDLAID Central Server Installer")

    config = {}
    country_scope = collect_country_scope()
    config.update(country_scope)
    config.update(collect_geo_level_names(country_scope["country_codes"]))
    config.update(collect_secrets())
    config.update(collect_ports())
    config.update(collect_images())

    if not print_summary(config):
        print("Installation cancelled")
        sys.exit(0)

    env_written = write_env_file(config)
    if not env_written:
        print("Cannot proceed without writing .env -- stopping")
        sys.exit(0)

    run_docker_compose_up()
    run_migrations()
    run_dbt_seed_and_run()
    write_geo_level_config(config["level_configs"])
    print_final_summary(config)


if __name__ == "__main__":
    main()