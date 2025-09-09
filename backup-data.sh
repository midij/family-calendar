#!/bin/bash

# Family Calendar Daily Backup Script
# This script creates a daily backup of your family calendar database

set -e

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$HOME/family-calendar-backups"
DATA_DIR="$PROJECT_DIR/data"
TIMESTAMP=$(date +%Y%m%d)
BACKUP_NAME="family_calendar_${TIMESTAMP}.db"

echo "🔄 Starting Family Calendar daily backup..."
echo "   Project directory: $PROJECT_DIR"
echo "   Backup directory: $BACKUP_DIR"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if database file exists (try both locations)
DB_FILE=""
if [ -f "$DATA_DIR/family_calendar.db" ]; then
    DB_FILE="$DATA_DIR/family_calendar.db"
    echo "   Found database in data directory: $DB_FILE"
elif [ -f "$PROJECT_DIR/family_calendar.db" ]; then
    DB_FILE="$PROJECT_DIR/family_calendar.db"
    echo "   Found database in project root: $DB_FILE"
else
    echo "❌ Database file not found in either location:"
    echo "   - $DATA_DIR/family_calendar.db"
    echo "   - $PROJECT_DIR/family_calendar.db"
    echo "   Make sure the Family Calendar has been used and has data."
    exit 1
fi

# Create backup
echo "📦 Creating backup: $BACKUP_NAME"
cp "$DB_FILE" "$BACKUP_DIR/$BACKUP_NAME"

# Get backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)

echo "✅ Backup completed successfully!"
echo "   Backup location: $BACKUP_DIR/$BACKUP_NAME"
echo "   Backup size: $BACKUP_SIZE"
echo ""

# List recent backups (keep last 7 days)
echo "📋 Recent backups:"
ls -la "$BACKUP_DIR" | tail -5

# Clean up old backups (keep last 30 days)
echo "🧹 Cleaning up old backups (keeping last 30 days)..."
find "$BACKUP_DIR" -name "family_calendar_*.db" -mtime +30 -delete 2>/dev/null || true

echo ""
echo "💡 To restore from backup:"
echo "   cp $BACKUP_DIR/$BACKUP_NAME $DATA_DIR/family_calendar.db"
echo "   docker-compose -f docker-compose.prod.yml restart"
