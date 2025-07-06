#!/bin/bash
# scripts/backup.sh
# SDX Project Manager - Automated Backup Script
# Comprehensive backup solution for production environment

set -euo pipefail

# ============================================================================
# CONFIGURATION VARIABLES
# ============================================================================

# Backup configuration
BACKUP_DIR="/backups"
RETENTION_DAYS=30
BACKUP_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DATE=$(date +"%Y-%m-%d %H:%M:%S")

# Database configuration
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-sdx_project_manager}"
DB_USER="${DB_USER:-sdx_user}"

# Application configuration
APP_NAME="sdx-project-manager"
LOG_FILE="$BACKUP_DIR/backup.log"

# Notification configuration
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
EMAIL_RECIPIENTS="${EMAIL_RECIPIENTS:-}"
NOTIFICATION_ENABLED="${NOTIFICATION_ENABLED:-false}"

# Cloud storage configuration (optional)
AWS_S3_BUCKET="${AWS_S3_BUCKET:-}"
AZURE_STORAGE_ACCOUNT="${AZURE_STORAGE_ACCOUNT:-}"
GOOGLE_CLOUD_BUCKET="${GOOGLE_CLOUD_BUCKET:-}"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Error handling function
error_exit() {
    local message="$1"
    log "ERROR" "$message"
    send_notification "❌ Backup Failed" "$message" "danger"
    exit 1
}

# Success notification
success_notification() {
    local message="$1"
    log "INFO" "$message"
    send_notification "✅ Backup Successful" "$message" "good"
}

# Send notification function
send_notification() {
    local title="$1"
    local message="$2"
    local color="${3:-good}"
    
    if [[ "$NOTIFICATION_ENABLED" == "true" ]]; then
        # Slack notification
        if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
            curl -X POST -H 'Content-type: application/json' \
                --data "{
                    \"text\":\"$title\",
                    \"attachments\":[{
                        \"color\":\"$color\",
                        \"fields\":[{
                            \"title\":\"Environment\",
                            \"value\":\"Production\",
                            \"short\":true
                        },{
                            \"title\":\"Timestamp\",
                            \"value\":\"$BACKUP_DATE\",
                            \"short\":true
                        },{
                            \"title\":\"Details\",
                            \"value\":\"$message\",
                            \"short\":false
                        }]
                    }]
                }" \
                "$SLACK_WEBHOOK_URL" || log "WARN" "Failed to send Slack notification"
        fi
        
        # Email notification (if configured)
        if [[ -n "$EMAIL_RECIPIENTS" ]] && command -v mail >/dev/null 2>&1; then
            echo "$message" | mail -s "$title - $APP_NAME" "$EMAIL_RECIPIENTS" || \
                log "WARN" "Failed to send email notification"
        fi
    fi
}

# Size formatting function
format_size() {
    local bytes=$1
    local units=("B" "KB" "MB" "GB" "TB")
    local unit=0
    
    while (( bytes >= 1024 && unit < ${#units[@]} - 1 )); do
        bytes=$((bytes / 1024))
        ((unit++))
    done
    
    echo "${bytes}${units[$unit]}"
}

# Check disk space
check_disk_space() {
    local required_space_gb="$1"
    local available_space=$(df "$BACKUP_DIR" | awk 'NR==2 {print $4}')
    local available_space_gb=$((available_space / 1024 / 1024))
    
    if (( available_space_gb < required_space_gb )); then
        error_exit "Insufficient disk space. Required: ${required_space_gb}GB, Available: ${available_space_gb}GB"
    fi
    
    log "INFO" "Disk space check passed. Available: ${available_space_gb}GB"
}

# ============================================================================
# BACKUP FUNCTIONS
# ============================================================================

# Database backup function
backup_database() {
    log "INFO" "Starting database backup..."
    
    local backup_file="$BACKUP_DIR/database_${BACKUP_TIMESTAMP}.sql"
    local compressed_file="${backup_file}.gz"
    
    # Check if database is accessible
    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"; then
        error_exit "Database is not accessible"
    fi
    
    # Create database dump
    if ! pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --verbose --clean --if-exists --create --format=plain > "$backup_file"; then
        error_exit "Database backup failed"
    fi
    
    # Compress the backup
    if ! gzip "$backup_file"; then
        error_exit "Database backup compression failed"
    fi
    
    local backup_size=$(stat -f%z "$compressed_file" 2>/dev/null || stat -c%s "$compressed_file")
    log "INFO" "Database backup completed: $(basename "$compressed_file") ($(format_size "$backup_size"))"
    
    echo "$compressed_file"
}

# Application data backup function
backup_application_data() {
    log "INFO" "Starting application data backup..."
    
    local backup_file="$BACKUP_DIR/app_data_${BACKUP_TIMESTAMP}.tar.gz"
    local app_data_dirs=(
        "/app/data/uploads"
        "/app/data/cache"
        "/app/logs"
        "/app/config"
        "/app/.streamlit"
    )
    
    # Create application data backup
    local existing_dirs=()
    for dir in "${app_data_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            existing_dirs+=("$dir")
        fi
    done
    
    if [[ ${#existing_dirs[@]} -eq 0 ]]; then
        log "WARN" "No application data directories found"
        return
    fi
    
    if ! tar -czf "$backup_file" "${existing_dirs[@]}" 2>/dev/null; then
        error_exit "Application data backup failed"
    fi
    
    local backup_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_