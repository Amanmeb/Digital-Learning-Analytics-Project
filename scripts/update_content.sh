#!/bin/bash
# Updates Moodle content from the latest backup file
# Downloads from central server or USB drive
# Restores into existing Moodle installation

set -e

CENTRAL_URL="${CENTRAL_API_URL:-http://central-server:8000}"
BACKUP_DIR="/home/ubuntu/cdlaid-backups"
BACKUP_FILE="${BACKUP_DIR}/master_cdlaid_moodle.mbz"

echo "Updating Moodle content"
echo "========================"

mkdir -p "${BACKUP_DIR}"

# Try central server first
echo "Downloading content backup from central server"
if curl -f -o "${BACKUP_FILE}" "${CENTRAL_URL}/content/master_cdlaid_moodle.mbz" 2>/dev/null; then
    echo "Downloaded from central server"
else
    echo "Central server not available -- checking USB drive"
    USB_PATH="/media/ubuntu/CDLAID/master_cdlaid_moodle.mbz"
    if [ -f "${USB_PATH}" ]; then
        cp "${USB_PATH}" "${BACKUP_FILE}"
        echo "Copied from USB drive"
    else
        echo "No backup source available -- exiting"
        exit 1
    fi
fi

echo "Restoring content backup into Moodle"
docker exec -u www-data cdlaid_moodle php /var/www/html/admin/cli/restore_backup.php     --file="/backups/master_cdlaid_moodle.mbz"     --categoryid=1

echo "Content update complete at $(date)"
