#!/bin/bash
# CDLAID School Server Installation Script
# Installs and configures a new school server
# Expected completion time: 20-25 minutes
# Run as: bash scripts/install_school.sh

set -e

echo ""
echo "CDLAID School Server Installation"
echo "==================================="
echo ""

# ------------------------------------------------------------
# Phase 1 -- Collect configuration (5 questions)
# ------------------------------------------------------------
echo "Phase 1 -- Configuration"
echo ""

read -p "School name: " SCHOOL_NAME
read -p "School ID (format ET-AA-001): " SCHOOL_ID
read -p "Central server URL (e.g. http://192.168.1.100:8000): " CENTRAL_URL
read -p "API key: " API_KEY
read -p "Moodle admin password: " MOODLE_ADMIN_PASSWORD

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
if [ "${OS_VERSION}" != "22.04" ]; then
    echo "WARNING: Expected Ubuntu 22.04 -- found ${OS_VERSION}"
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
MOODLE_ADMIN_PASSWORD=${MOODLE_ADMIN_PASSWORD}
QUEUE_DB_PATH=/opt/cdlaid/edge/queue.db
XAPI_HOMEPAGE_URL=${CENTRAL_URL}
EOF

echo "Environment file created"

# ------------------------------------------------------------
# Phase 3 -- Start Moodle and MySQL
# ------------------------------------------------------------
echo "Phase 3 -- Starting Moodle"

cd "${REPO_DIR}"
docker compose -f docker-compose.school.yml up -d

echo "Waiting for Moodle to start (this takes 2-3 minutes)"
sleep 120

# ------------------------------------------------------------
# Phase 4 -- Content import
# ------------------------------------------------------------
echo "Phase 4 -- Content import"

BACKUP_DIR="/home/ubuntu/cdlaid-backups"
mkdir -p "${BACKUP_DIR}"

# Try central server first
if curl -f -o "${BACKUP_DIR}/master_cdlaid_moodle.mbz"     "${CENTRAL_URL}/content/master_cdlaid_moodle.mbz" 2>/dev/null; then
    echo "Master backup downloaded from central server"
else
    echo "Central server not available -- checking USB"
    USB_PATH="/media/ubuntu/CDLAID/master_cdlaid_moodle.mbz"
    if [ -f "${USB_PATH}" ]; then
        cp "${USB_PATH}" "${BACKUP_DIR}/master_cdlaid_moodle.mbz"
        echo "Master backup copied from USB"
    else
        echo "No backup available -- skipping content import"
    fi
fi

# ------------------------------------------------------------
# Phase 5 -- Configure xAPI plugin
# ------------------------------------------------------------
echo "Phase 5 -- Configuring xAPI plugin"

docker exec -u www-data cdlaid_moodle php     /var/www/html/admin/cli/cfg.php     --component=logstore_xapi     --name=endpoint     --set="${CENTRAL_URL}/xapi/statements"

docker exec -u www-data cdlaid_moodle php     /var/www/html/admin/cli/cfg.php     --component=logstore_xapi     --name=username     --set="${API_KEY}"

# Register school with central server
echo "Registering school with central server"
curl -s -X POST "${CENTRAL_URL}/api/v1/admin/schools"     -H "Content-Type: application/json"     -H "X-API-Key: ${API_KEY}"     -d "{"school_id":"${SCHOOL_ID}","school_name":"${SCHOOL_NAME}","region_id":"ET-AA"}"     || echo "School registration will retry on first sync"

# ------------------------------------------------------------
# Phase 6 -- Install sync agent as systemd service
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

echo "Moodle status:"
curl -s -o /dev/null -w "  HTTP %{http_code}\n" http://localhost:3000

echo "Sync monitor status:"
curl -s http://localhost:8090/status | python3 -m json.tool || echo "  Not yet ready"

echo ""
echo "Installation complete"
echo "====================="
echo "  School:       ${SCHOOL_NAME}"
echo "  School ID:    ${SCHOOL_ID}"
echo "  Moodle:       http://localhost:3000"
echo "  Sync monitor: http://localhost:8090/status"
echo ""
echo "Total time: approximately 25 minutes"


# ------------------------------------------------------------
# Phase 8 -- WiFi Hotspot Setup
# NOTE: Ubuntu only -- requires nmcli and WiFi adapter
# Tested on Ubuntu 22.04 LTS with built-in WiFi adapter
# ------------------------------------------------------------
echo "Phase 8 -- WiFi Hotspot Setup"

# Check if nmcli is available
if ! command -v nmcli &> /dev/null; then
    echo "nmcli not found -- skipping hotspot setup"
    echo "Install with: sudo apt-get install network-manager"
else
    # Generate hotspot name from school ID
    HOTSPOT_NAME="Camara-${SCHOOL_ID}"
    HOTSPOT_PASSWORD="camara${SCHOOL_ID//[-]}"

    # Check if WiFi adapter is available
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

        # Enable autostart on boot
        nmcli connection modify "${HOTSPOT_NAME}" connection.autoconnect yes

        echo ""
        echo "Hotspot configured:"
        echo "  Network name: ${HOTSPOT_NAME}"
        echo "  Password:     ${HOTSPOT_PASSWORD}"
        echo "  Server IP:    10.42.0.1"
        echo "  Moodle URL:   http://10.42.0.1:3000"
        echo "  Export URL:   http://10.42.0.1:8090/export"
        echo ""
        echo "Students connect their devices to ${HOTSPOT_NAME}"
        echo "then open http://10.42.0.1:3000 in their browser"

        # Update Moodle wwwroot to use hotspot IP
        docker exec -u www-data cdlaid_moodle php \
            /var/www/html/admin/cli/cfg.php \
            --name=wwwroot \
            --set="http://10.42.0.1:3000" \
            && echo "Moodle wwwroot updated to http://10.42.0.1:3000" \
            || echo "Could not update Moodle wwwroot -- update manually"

        # Print QR code hint
        echo ""
        echo "Tip: Generate a QR code for http://10.42.0.1:3000"
        echo "     and post it in every classroom"
    fi
fi

echo ""
echo "==================================="
echo "Installation complete"
echo "==================================="
echo "  School:       ${SCHOOL_NAME}"
echo "  School ID:    ${SCHOOL_ID}"
echo "  Moodle:       http://10.42.0.1:3000"
echo "  Sync monitor: http://10.42.0.1:8090/status"
echo "  Data export:  http://10.42.0.1:8090/export"
echo "==================================="