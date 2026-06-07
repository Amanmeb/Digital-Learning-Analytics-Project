#!/bin/bash
# Daily PostgreSQL backup script
# Runs at 1am via cron
# Keeps 30 days of backups
# Backup format: cdlaid_backup_YYYYMMDD.sql.gz

set -e

BACKUP_DIR="/home/ubuntu/cdlaid-backups"
DB_NAME="cdlaid_analytics"
DB_USER="cdlaid_user"
DATE=$(date +%Y%m%d)
BACKUP_FILE="${BACKUP_DIR}/cdlaid_backup_${DATE}.sql.gz"
RETENTION_DAYS=30

mkdir -p "${BACKUP_DIR}"

echo "Starting backup: ${BACKUP_FILE}"

docker exec cdlaid_postgres pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip > "${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    echo "Backup complete: ${BACKUP_FILE}"
else
    echo "Backup failed"
    exit 1
fi

# Remove backups older than retention days
find "${BACKUP_DIR}" -name "cdlaid_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
echo "Old backups cleaned up -- keeping last ${RETENTION_DAYS} days"

echo "Backup finished at $(date)"
