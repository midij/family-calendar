#!/bin/bash

# Setup Daily Backup for Family Calendar
# This script sets up automated daily backups using cron

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$PROJECT_DIR/backup-data.sh"
CRON_JOB="0 2 * * * cd $PROJECT_DIR && $BACKUP_SCRIPT >> ~/family-calendar-backups/backup.log 2>&1"

echo "🔄 Setting up daily backup for Family Calendar..."

# Make backup script executable
chmod +x "$BACKUP_SCRIPT"

# Create backup directory
mkdir -p ~/family-calendar-backups

# Test the backup script
echo "🧪 Testing backup script..."
if "$BACKUP_SCRIPT"; then
    echo "✅ Backup script test successful!"
else
    echo "❌ Backup script test failed. Please check the script."
    exit 1
fi

# Add to crontab
echo "📅 Adding daily backup to crontab..."
echo "   Cron job: $CRON_JOB"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "backup-data.sh"; then
    echo "⚠️  Daily backup already exists in crontab."
    echo "   Current cron jobs:"
    crontab -l | grep "backup-data.sh"
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Daily backup added to crontab!"
    echo "   Backup will run daily at 2:00 AM"
fi

echo ""
echo "📋 Current cron jobs:"
crontab -l | grep -E "(backup-data|family-calendar)" || echo "   No family calendar cron jobs found"

echo ""
echo "💡 Manual backup: $BACKUP_SCRIPT"
echo "💡 View backup log: tail -f ~/family-calendar-backups/backup.log"
echo "💡 Remove daily backup: crontab -e (then delete the line)"
