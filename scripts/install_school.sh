#!/bin/bash
# CDLAID School Server Installation Script
# Installs and configures a new school server for direct device tracking
# Moodle has been fully removed from this project -- login_app (port
# 3000) is the student-facing entry point, replacing it entirely
# Expected completion time: 20-25 minutes
# Run as: bash scripts/install_school.sh

set -e

echo ""
echo "CDLAID School Server Installation"
echo "==================================="
echo ""

# ------------------------------------------------------------
# Phase 1 -- Collect configuration
# ------------------------------------------------------------
echo "Phase 1 -- Configuration"
echo ""

read -p "School name: " SCHOOL_NAME
read -p "School ID (format ET-AA-001): " SCHOOL_ID
read -p "Central server URL (e.g. http://192.168.1.100:8000): " CENTRAL_URL
read -p "API key: " API_KEY
read -p "Admin API key for login_app (used for student registration endpoints): " ADMIN_API_KEY

SERVER_ID="SRV-${SCHOOL_ID}-001"
DEVICE_ID="DEV-${SCHOOL_ID}-000001"

echo ""
echo "Configuration:"
echo "  School name:  ${SCHOOL_NAME}"
echo "  School ID:    ${SCHOOL_ID}"
echo "  Server ID:    ${SERVER_ID}"
echo "  Central URL:  ${CENTRAL_URL}"
echo ""

# ------------------------------------------------------------
# Phase 2 -- System setup
# ------------------------------------------------------------
echo "Phase 2 -- System setup"

# Check Ubuntu version
OS_VERSION=$(lsb_release -rs)
if [ "${OS_VERSION}" != "22.04" ] && [ "${OS_VERSION}" != "24.04" ]; then
    echo "WARNING: Expected Ubuntu 22.04 or 24.04 -- found ${OS_VERSION}"
fi

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker"
    apt-get update -qq
    apt-get install -y -qq docker.io
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ubuntu
fi

# Clone or update repository
REPO_DIR="/opt/cdlaid"
if [ -d "${REPO_DIR}" ]; then
    echo "Updating existing repository"
    cd "${REPO_DIR}"
    git pull origin main
else
    echo "Cloning repository"
    git clone https://github.com/Amanmeb/Digital-Learning-Analytics-Project.git "${REPO_DIR}"
    cd "${REPO_DIR}"
fi

# Create school environment file
cat > "${REPO_DIR}/.env.school" << EOF
SCHOOL_ID=${SCHOOL_ID}
SCHOOL_NAME=${SCHOOL_NAME}
SERVER_ID=${SERVER_ID}
DEVICE_ID=${DEVICE_ID}
CENTRAL_API_URL=${CENTRAL_URL}
API_SECRET_KEY=${API_KEY}
ADMIN_API_KEY=${ADMIN_API_KEY}
QUEUE_DB_PATH=/opt/cdlaid/edge/queue.db
XAPI_HOMEPAGE_URL=${CENTRAL_URL}
EOF

echo "Environment file created"

# ------------------------------------------------------------
# Phase 3 -- Start school stack (postgres, superset, device
# receiver, login_app)
# ------------------------------------------------------------
echo "Phase 3 -- Starting school stack"

cd "${REPO_DIR}"
docker compose -f docker-compose.school.yml up -d

echo "Waiting for school postgres to become healthy"
for i in $(seq 1 30); do
    if docker exec cdlaid_school_postgres pg_isready -U cdlaid_user > /dev/null 2>&1; then
        echo "School postgres is ready"
        break
    fi
    sleep 5
done

# ------------------------------------------------------------
# Phase 4 -- Apply database schema migrations
# Runs every migration file in sql/migrations in order. Every
# migration in this project is written to be safe to re-run
# (IF NOT EXISTS / ON CONFLICT DO NOTHING), so this is safe on
# both a brand new database and one being updated.
# ------------------------------------------------------------
echo "Phase 4 -- Applying database schema"

for migration_file in "${REPO_DIR}"/sql/migrations/*.sql; do
    echo "  Applying $(basename "${migration_file}")"
    docker exec -i -e PGPASSWORD="${POSTGRES_PASSWORD:-CdlaidDB2025!Strong}" \
        cdlaid_school_postgres psql -U cdlaid_user -d cdlaid_school \
        < "${migration_file}" \
        || echo "    WARNING: migration $(basename "${migration_file}") reported an error -- review manually"
done

echo "Schema migrations applied"

# ------------------------------------------------------------
# Phase 5 -- Register school with central server
# ------------------------------------------------------------
echo "Phase 5 -- Registering school with central server"

curl -s -X POST "${CENTRAL_URL}/api/v1/admin/schools" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: ${API_KEY}" \
    -d "{\"school_id\":\"${SCHOOL_ID}\",\"school_name\":\"${SCHOOL_NAME}\"}" \
    || echo "School registration will retry on first sync"

echo ""
echo "Note: this school has no zone/woreda assignment yet. Assign one"
echo "later via the geo admin endpoints in login_app once real"
echo "administrative data is available:"
echo "  GET  ${CENTRAL_URL}/admin/geo/zones"
echo "  POST /admin/schools/${SCHOOL_ID}/woreda"

# ------------------------------------------------------------
# Phase 6 -- Install sync agent and monitor as systemd services
# ------------------------------------------------------------
echo "Phase 6 -- Installing sync agent"

cat > /etc/systemd/system/cdlaid-sync-agent.service << EOF
[Unit]
Description=CDLAID Sync Agent
After=network.target docker.service
Wants=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/cdlaid
EnvironmentFile=/opt/cdlaid/.env.school
ExecStart=/usr/bin/python3 -m edge.sync_agent
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/cdlaid-sync-monitor.service << EOF
[Unit]
Description=CDLAID School Status Monitor
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/cdlaid
EnvironmentFile=/opt/cdlaid/.env.school
ExecStart=/usr/bin/python3 -m edge.sync_monitor
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cdlaid-sync-agent
systemctl enable cdlaid-sync-monitor
systemctl start cdlaid-sync-agent
systemctl start cdlaid-sync-monitor

# ------------------------------------------------------------
# Phase 7 -- Verification
# ------------------------------------------------------------
echo ""
echo "Phase 7 -- Verification"

echo "Login app status:"
curl -s -o /dev/null -w "  HTTP %{http_code}\n" http://localhost:3000/login

echo "Device receiver status:"
curl -s -o /dev/null -w "  HTTP %{http_code}\n" http://localhost:8001/api/v1/device/ingest -X POST -H "Content-Type: application/json" -d "[]"

echo "Sync monitor status:"
curl -s http://localhost:8090/status | python3 -m json.tool || echo "  Not yet ready"

# ------------------------------------------------------------
# Phase 8 -- Network Connection Setup
# NOTE: Ubuntu only -- requires nmcli and WiFi adapter
# Tested on Ubuntu 22.04 LTS with built-in WiFi adapter
# Supports three connection methods:
#   Option 1 -- Hotspot only (default for most schools)
#   Option 2 -- LAN/ethernet only (schools with existing network)
#   Option 3 -- Both hotspot and LAN simultaneously
# Connection method and LAN IP stored in .env.school for later changes
# ------------------------------------------------------------
echo ""
echo "Phase 8 -- Network Connection Setup"
echo ""
echo "Choose connection method:"
echo "  1 -- Hotspot only (students connect to school WiFi hotspot)"
echo "  2 -- LAN/ethernet only (school has existing wired network)"
echo "  3 -- Both hotspot and LAN simultaneously"
echo ""
read -p "Enter choice (1, 2, or 3): " CONNECTION_CHOICE

# Validate choice
if [ "${CONNECTION_CHOICE}" != "1" ] && \
   [ "${CONNECTION_CHOICE}" != "2" ] && \
   [ "${CONNECTION_CHOICE}" != "3" ]; then
    echo "Invalid choice -- defaulting to Option 1 (hotspot only)"
    CONNECTION_CHOICE="1"
fi

# Set connection method label
case "${CONNECTION_CHOICE}" in
    1) CONNECTION_METHOD="hotspot" ;;
    2) CONNECTION_METHOD="lan" ;;
    3) CONNECTION_METHOD="both" ;;
esac

echo "Selected: ${CONNECTION_METHOD}"

# Collect LAN IP if needed
LAN_IP=""
if [ "${CONNECTION_CHOICE}" = "2" ] || [ "${CONNECTION_CHOICE}" = "3" ]; then
    echo ""
    read -p "Enter LAN IP address for this server (e.g. 192.168.1.100): " LAN_IP
    if [ -z "${LAN_IP}" ]; then
        echo "WARNING: No LAN IP entered -- skipping LAN configuration"
        if [ "${CONNECTION_CHOICE}" = "2" ]; then
            echo "Falling back to hotspot only"
            CONNECTION_METHOD="hotspot"
            CONNECTION_CHOICE="1"
        fi
    fi
fi

# Store connection config in .env.school
echo "CONNECTION_METHOD=${CONNECTION_METHOD}" >> "${REPO_DIR}/.env.school"
echo "LAN_IP=${LAN_IP}" >> "${REPO_DIR}/.env.school"

# ------------------------------------------------------------
# Hotspot setup -- runs for Option 1 and Option 3
# ------------------------------------------------------------
HOTSPOT_CONFIGURED=false

if [ "${CONNECTION_CHOICE}" = "1" ] || [ "${CONNECTION_CHOICE}" = "3" ]; then

    if ! command -v nmcli &> /dev/null; then
        echo "nmcli not found -- skipping hotspot setup"
        echo "Install with: sudo apt-get install network-manager"
    else
        HOTSPOT_NAME="Camara-${SCHOOL_ID}"
        HOTSPOT_PASSWORD="camara${SCHOOL_ID//[-]}"

        WIFI_ADAPTER=$(nmcli device status | grep wifi | head -1 | awk '{print $1}')
        if [ -z "${WIFI_ADAPTER}" ]; then
            echo "No WiFi adapter found -- skipping hotspot setup"
        else
            echo "Setting up hotspot on adapter: ${WIFI_ADAPTER}"

            # Delete existing hotspot connection if present
            nmcli connection delete "${HOTSPOT_NAME}" 2>/dev/null || true

            # Create new hotspot connection
            nmcli connection add \
                type wifi \
                ifname "${WIFI_ADAPTER}" \
                con-name "${HOTSPOT_NAME}" \
                autoconnect yes \
                ssid "${HOTSPOT_NAME}" \
                -- \
                wifi.mode ap \
                wifi-sec.key-mgmt wpa-psk \
                wifi-sec.psk "${HOTSPOT_PASSWORD}" \
                ipv4.method shared \
                ipv4.addresses "10.42.0.1/24"

            # Enable hotspot
            nmcli connection up "${HOTSPOT_NAME}"
            nmcli connection modify "${HOTSPOT_NAME}" connection.autoconnect yes

            HOTSPOT_CONFIGURED=true

            echo ""
            echo "Hotspot configured:"
            echo "  Network name: ${HOTSPOT_NAME}"
            echo "  Password:     ${HOTSPOT_PASSWORD}"
            echo "  Server IP:    10.42.0.1"
            echo ""
        fi
    fi
fi

# ------------------------------------------------------------
# LAN setup -- runs for Option 2 and Option 3
# ------------------------------------------------------------
LAN_CONFIGURED=false

if [ "${CONNECTION_CHOICE}" = "2" ] || [ "${CONNECTION_CHOICE}" = "3" ]; then
    if [ -n "${LAN_IP}" ]; then
        echo "LAN configuration:"
        echo "  LAN IP: ${LAN_IP}"
        echo "  Students access login app at http://${LAN_IP}:3000"
        echo "  Sync monitor at http://${LAN_IP}:8090"
        echo "  Install page at http://${LAN_IP}:8090/install"
        LAN_CONFIGURED=true
        echo "LAN IP stored in .env.school"
    fi
fi

# ------------------------------------------------------------
# Determine login app URL based on connection method
# Priority: hotspot IP if hotspot is configured, otherwise LAN IP
# ------------------------------------------------------------
if [ "${HOTSPOT_CONFIGURED}" = "true" ]; then
    LOGIN_APP_URL="http://10.42.0.1:3000"
elif [ "${LAN_CONFIGURED}" = "true" ] && [ -n "${LAN_IP}" ]; then
    LOGIN_APP_URL="http://${LAN_IP}:3000"
else
    LOGIN_APP_URL="http://localhost:3000"
fi

echo "LOGIN_APP_URL=${LOGIN_APP_URL}" >> "${REPO_DIR}/.env.school"

# Print QR code hint
if [ "${HOTSPOT_CONFIGURED}" = "true" ] || [ "${LAN_CONFIGURED}" = "true" ]; then
    echo ""
    echo "Tip: Generate a QR code for ${LOGIN_APP_URL}/login"
    echo "     and post it in every classroom"
    echo "     Or visit http://10.42.0.1:8090/install for device setup"
fi

# ------------------------------------------------------------
# Final summary
# ------------------------------------------------------------
echo ""
echo "==================================="
echo "Installation complete"
echo "==================================="
echo "  School:            ${SCHOOL_NAME}"
echo "  School ID:         ${SCHOOL_ID}"
echo "  Connection method: ${CONNECTION_METHOD}"
echo "  Login app URL:     ${LOGIN_APP_URL}/login"
if [ -n "${LAN_IP}" ]; then
    echo "  LAN IP:            ${LAN_IP}"
fi
echo "  Sync monitor:      http://10.42.0.1:8090/status"
echo "  Data export:       http://10.42.0.1:8090/export"
echo "  Device install:    http://10.42.0.1:8090/install"
echo "==================================="
echo ""
echo "Zone/woreda assignment for this school is not yet set -- assign"
echo "one via the geo admin endpoints once real administrative data"
echo "is available (see Phase 5 above)."
echo ""
echo "To change connection method later:"
echo "  Edit /opt/cdlaid/.env.school"
echo "  Update CONNECTION_METHOD and LAN_IP"
echo "  Then re-run: bash scripts/install_school.sh"
echo "==================================="