#!/bin/bash
# Updates a school server to the latest version
# Pulls latest code from GitHub and restarts services

set -e

REPO_DIR="/opt/cdlaid"
BRANCH="main"

echo "Updating school server"
echo "======================"

cd "${REPO_DIR}"

echo "Pulling latest code from GitHub"
git fetch origin
git checkout "${BRANCH}"
git pull origin "${BRANCH}"

echo "Restarting sync agent"
systemctl restart cdlaid-sync-agent

echo "Restarting school status monitor"
systemctl restart cdlaid-sync-monitor

echo "Update complete at $(date)"
