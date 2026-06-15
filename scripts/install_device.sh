#!/bin/bash
# CDLAID Device Agent Installer for Linux
# Installs the device agent as a systemd service
# Run as: sudo bash scripts/install_device.sh
# Tested on Ubuntu 22.04 LTS

set -e

echo ""
echo "CDLAID Device Agent Installer for Linux"
echo "========================================="
echo ""

# ------------------------------------------------------------
# Check for root privileges
# ------------------------------------------------------------

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: This script must be run as root"
    echo "Run as: sudo bash scripts/install_device.sh"
    exit 1
fi

# ------------------------------------------------------------
# Collect configuration
# ------------------------------------------------------------

read -p "Enter School ID (e.g. ET-AA-001): " SCHOOL_ID
read -p "Enter Server ID (e.g. SRV-ET-AA-001-001): " SERVER_ID
read -p "Enter Device ID (e.g. DEV-ET-AA-001-000001): " DEVICE_ID
read -p "Enter School API Key: " SCHOOL_API_KEY

echo ""
echo "Configuration:"
echo "  School ID:  ${SCHOOL_ID}"
echo "  Server ID:  ${SERVER_ID}"
echo "  Device ID:  ${DEVICE_ID}"
echo ""

# ------------------------------------------------------------
# Check Python is installed
# ------------------------------------------------------------

if ! command -v python3 &> /dev/null; then
    echo "Python3 not found -- installing"
    apt-get update -qq
    apt-get install -y -qq python3 python3-pip
fi

echo "Python found: $(python3 --version)"

# ------------------------------------------------------------
# Install required Python packages
# ------------------------------------------------------------

echo ""
echo "Installing required packages"
pip3 install requests --quiet --break-system-packages 2>/dev/null \
    || pip3 install requests --quiet
echo "Packages installed"

# ------------------------------------------------------------
# Create installation directory
# ------------------------------------------------------------

echo ""
echo "Creating installation directory"

mkdir -p /opt/cdlaid
mkdir -p /opt/cdlaid/logs

echo "Directory created: /opt/cdlaid"

# ------------------------------------------------------------
# Copy device agent to installation directory
# ------------------------------------------------------------

echo ""
echo "Copying device agent"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"

if [ -f "${PROJECT_DIR}/edge/device_agent.py" ]; then
    cp "${PROJECT_DIR}/edge/device_agent.py" /opt/cdlaid/device_agent.py
    echo "Device agent copied from ${PROJECT_DIR}/edge/device_agent.py"
elif [ -f "/opt/cdlaid-repo/edge/device_agent.py" ]; then
    cp /opt/cdlaid-repo/edge/device_agent.py /opt/cdlaid/device_agent.py
    echo "Device agent copied from /opt/cdlaid-repo/edge/device_agent.py"
else
    echo "ERROR: device_agent.py not found"
    echo "Make sure you are running this from the project root directory"
    exit 1
fi

echo "Device agent installed at /opt/cdlaid/device_agent.py"

# ------------------------------------------------------------
# Write environment configuration file
# ------------------------------------------------------------

echo ""
echo "Writing configuration"

cat > /opt/cdlaid/device_agent.env << EOF
SCHOOL_ID=${SCHOOL_ID}
SERVER_ID=${SERVER_ID}
DEVICE_ID=${DEVICE_ID}
SCHOOL_API_KEY=${SCHOOL_API_KEY}
RECEIVER_URL=http://10.42.0.1:8000/api/v1/device/ingest
HOTSPOT_IP=10.42.0.1
SYNC_INTERVAL_SECONDS=60
SYNC_BATCH_SIZE=200
DEVICE_QUEUE_PATH=/opt/cdlaid/device_queue.db
EOF

chmod 600 /opt/cdlaid/device_agent.env
echo "Configuration written to /opt/cdlaid/device_agent.env"

# ------------------------------------------------------------
# Write systemd service file
# ------------------------------------------------------------

echo ""
echo "Writing systemd service"

cat > /etc/systemd/system/cdlaid-device-agent.service << EOF
[Unit]
Description=CDLAID Device Agent
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/cdlaid
EnvironmentFile=/opt/cdlaid/device_agent.env
ExecStart=/usr/bin/python3 /opt/cdlaid/device_agent.py
Restart=always
RestartSec=30
StandardOutput=append:/opt/cdlaid/logs/device_agent.log
StandardError=append:/opt/cdlaid/logs/device_agent.log

[Install]
WantedBy=multi-user.target
EOF

echo "Systemd service written to /etc/systemd/system/cdlaid-device-agent.service"

# ------------------------------------------------------------
# Enable and start the service
# ------------------------------------------------------------

echo ""
echo "Enabling and starting service"

systemctl daemon-reload
systemctl enable cdlaid-device-agent
systemctl start cdlaid-device-agent

echo "Service enabled and started"

# ------------------------------------------------------------
# Verify installation
# ------------------------------------------------------------

echo ""
echo "Verifying installation"

if [ -f "/opt/cdlaid/device_agent.py" ]; then
    echo "  device_agent.py      OK"
else
    echo "  device_agent.py      MISSING"
fi

if [ -f "/opt/cdlaid/device_agent.env" ]; then
    echo "  device_agent.env     OK"
else
    echo "  device_agent.env     MISSING"
fi

if [ -f "/etc/systemd/system/cdlaid-device-agent.service" ]; then
    echo "  systemd service      OK"
else
    echo "  systemd service      MISSING"
fi

sleep 2
if systemctl is-active --quiet cdlaid-device-agent; then
    echo "  service running      OK"
else
    echo "  service running      FAILED -- check logs below"
    journalctl -u cdlaid-device-agent --no-pager -n 20
fi

echo ""
echo "========================================="
echo "Installation complete"
echo "========================================="
echo "  School ID:    ${SCHOOL_ID}"
echo "  Device ID:    ${DEVICE_ID}"
echo "  Queue:        /opt/cdlaid/device_queue.db"
echo "  Logs:         /opt/cdlaid/logs/device_agent.log"
echo "  Service:      cdlaid-device-agent"
echo "========================================="
echo ""
echo "The agent will sync automatically when connected"
echo "to the school hotspot Camara-${SCHOOL_ID}"
echo ""
echo "Useful commands:"
echo "  Check status:  systemctl status cdlaid-device-agent"
echo "  View logs:     tail -f /opt/cdlaid/logs/device_agent.log"
echo "  Stop agent:    systemctl stop cdlaid-device-agent"
echo "  Start agent:   systemctl start cdlaid-device-agent"
echo ""