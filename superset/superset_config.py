import os

# Superset specific config
ROW_LIMIT = 5000
SUPERSET_WEBSERVER_PORT = 8088

# Secret key for signing cookies
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "cdlaid_superset_secret_key_2025_strong_random")

# Database connection for Superset metadata
SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://cdlaid_user:CdlaidDB2025!Strong@postgres:5432/cdlaid_analytics"

# Allow all origins for development
WTF_CSRF_ENABLED = False

# Feature flags
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "ENABLE_DASHBOARD_SCREENSHOT": True,
    "ALERT_REPORTS": True,
}

# Disable druid and other unused connectors
ADDITIONAL_MODULE_DS_MAP = {}

# Talisman config for development
TALISMAN_ENABLED = False

# Cache config
CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
}

# Brand
APP_NAME = "CDLAID Analytics"
APP_ICON = ""

# Webserver
WEBSERVER_ADDRESS = "0.0.0.0"

# Enable PDF and image export
ENABLE_SCHEDULED_EMAIL_REPORTS = True
EMAIL_REPORTS_WEBDRIVER = "selenium"

# Disable content security policy warning
CONTENT_SECURITY_POLICY_WARNING = False