import os

# School Superset configuration
# Lighter than central -- optimized for 4GB RAM school servers
# No screenshots, no scheduled reports, 1 worker, SimpleCache

ROW_LIMIT = 2000
SUPERSET_WEBSERVER_PORT = 8088

# Secret key for signing cookies
SECRET_KEY = os.environ.get(
    "SUPERSET_SECRET_KEY",
    "cdlaid_school_superset_secret_key_2025_strong"
)

# School PostgreSQL connection for Superset metadata
# Uses school postgres container name as host
SQLALCHEMY_DATABASE_URI = (
    "postgresql+psycopg2://cdlaid_user:CdlaidDB2025!Strong"
    "@cdlaid_school_postgres:5432/cdlaid_school"
)

# Disable CSRF for development
WTF_CSRF_ENABLED = False

# Feature flags -- lighter than central
# Screenshots and scheduled reports disabled to save RAM
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "ENABLE_DASHBOARD_SCREENSHOT": False,
    "ALERT_REPORTS": False,
}

# Disable unused connectors
ADDITIONAL_MODULE_DS_MAP = {}

# Disable Talisman for development
TALISMAN_ENABLED = False

# SimpleCache -- no Redis needed on school server
CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
}

# Brand
APP_NAME = "Camara School Analytics"
APP_ICON = ""

# Listen on all interfaces so hotspot devices can connect
WEBSERVER_ADDRESS = "0.0.0.0"

# Disable content security policy warning
CONTENT_SECURITY_POLICY_WARNING = False

# Disable email reports -- not needed on school server
ENABLE_SCHEDULED_EMAIL_REPORTS = False