# Deployment Guide

Comprehensive deployment documentation for Family Calendar.

## Table of Contents

- [Docker Deployment](#docker-deployment)
- [Bare-Metal Deployment](#bare-metal-deployment)
- [Updating Deployments](#updating-deployments)
- [Backup and Restore](#backup-and-restore)
- [Management Commands](#management-commands)
- [Troubleshooting](#troubleshooting)

## Docker Deployment

This is the recommended deployment method using containerization without modifying your system.

### Prerequisites

- Ubuntu/Debian server
- Docker and Docker Compose installed
- Ports 8080 and 8443 available

### Initial Deployment

```bash
# Clone the repository
git clone https://github.com/midij/family-calendar.git
cd family-calendar

# Run the deployment script
./deploy-docker.sh production
```

The script will:
- Create necessary directories (`data`, `logs`, `ssl`)
- Generate self-signed SSL certificates
- Build and start Docker containers
- Run database migrations
- Optionally seed sample data

### Access URLs

- Wall Display: `https://YOUR_SERVER_IP:8443/frontend/wall.html`
- Admin Interface: `https://YOUR_SERVER_IP:8443/frontend/admin.html`
- Health Check: `https://YOUR_SERVER_IP:8443/health`

### SSL Certificates

The deployment uses self-signed SSL certificates. For production, replace `ssl/cert.pem` and `ssl/key.pem` with real certificates from Let's Encrypt or your certificate provider.

## Bare-Metal Deployment

This method installs everything directly on your server with systemd and Nginx. Ideal for traditional server setups or when you need more control over system configuration.

### Prerequisites

- Ubuntu/Debian server
- Sudo privileges
- Ports 80 and 443 available

### Deployment Methods

**Method 1: Direct download (no git clone needed)**

```bash
# Download the script
curl -sSL https://raw.githubusercontent.com/midij/family-calendar/main/deploy.sh -o deploy.sh

# Make executable and run
chmod +x deploy.sh && ./deploy.sh production
```

**Method 2: Clone repository first**

```bash
# Clone the repository
git clone https://github.com/midij/family-calendar.git
cd family-calendar

# Run the deployment script
./deploy.sh production
```

### What the Script Does

The script automatically:
- Installs system dependencies (Python, Nginx, UFW, Certbot)
- Creates `/opt/family-calendar` directory
- Clones or updates the repository (includes `git pull` for updates!)
- Creates Python virtual environment
- Installs Python dependencies
- Runs database migrations
- Creates and starts systemd service
- Configures Nginx as reverse proxy
- Sets up firewall rules
- Configures logging and log rotation

### Access URLs

- Wall Display: `http://YOUR_SERVER_IP/frontend/wall.html`
- Admin Interface: `http://YOUR_SERVER_IP/frontend/admin.html`

### Post-Deployment Configuration

For production use with custom domain:

1. Configure your domain in `/etc/nginx/sites-available/family-calendar`
2. Set up SSL: `sudo certbot --nginx -d yourdomain.com`
3. Update CORS settings in `/opt/family-calendar/.env`
4. Restart the service: `sudo systemctl restart family-calendar`

## Updating Deployments

### Docker Updates

```bash
# 1. Navigate to your project directory
cd family-calendar

# 2. (Optional but recommended) Backup your data first
./backup-data.sh

# 3. Pull the latest changes
git pull origin main

# 4. Rebuild and restart containers
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# 5. Run any new database migrations
docker-compose -f docker-compose.prod.yml exec family-calendar alembic upgrade head

# 6. Verify the application is running
docker-compose -f docker-compose.prod.yml ps
```

**Important:** Your data is safe because it's stored in the `./data` volume, which persists across container rebuilds.

### Bare-Metal Updates

**Automatic (Recommended):**

The easiest way is to simply re-run the deployment script:

```bash
# 1. (Optional but recommended) Backup your data first
./backup-data.sh

# 2. Run the deployment script again
./deploy.sh production
```

The script will:
- Automatically pull the latest code (`git pull`)
- Update Python dependencies
- Run database migrations
- Restart the service
- **Your database is preserved** (it's in `.gitignore`)

**Manual Method:**

```bash
# 1. Backup data (recommended)
./backup-data.sh

# 2. Navigate to project directory
cd /opt/family-calendar

# 3. Pull latest changes
git pull origin main

# 4. Update Python dependencies
source venv/bin/activate
pip install -r requirements.txt

# 5. Run database migrations
alembic upgrade head

# 6. Restart the service
sudo systemctl restart family-calendar
sudo systemctl status family-calendar

# 7. Check logs if needed
sudo journalctl -u family-calendar -f
```

**Important:** Your database file `family_calendar.db` remains untouched during updates because it's ignored by git.

## Backup and Restore

### Automated Daily Backups

Set up automated daily backups using cron:

```bash
# Edit your crontab
crontab -e

# Add this line to run backups daily at 2 AM
0 2 * * * cd /path/to/family-calendar && ./backup-data.sh >> ~/family-calendar-backups/backup.log 2>&1
```

### Manual Backup

```bash
./backup-data.sh
```

Backups are stored in `~/family-calendar-backups/` with timestamps (e.g., `family_calendar_20260209.db`). Old backups (30+ days) are automatically cleaned up.

### Restore from Backup

**For Docker deployments:**

```bash
# Stop the application
docker-compose -f docker-compose.prod.yml down

# Restore the database
cp ~/family-calendar-backups/family_calendar_YYYYMMDD.db ./data/family_calendar.db

# Restart the application
docker-compose -f docker-compose.prod.yml up -d
```

**For bare-metal deployments:**

```bash
# Stop the service
sudo systemctl stop family-calendar

# Restore the database
cp ~/family-calendar-backups/family_calendar_YYYYMMDD.db /opt/family-calendar/family_calendar.db

# Start the service
sudo systemctl start family-calendar
```

## Management Commands

### Docker Deployments

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Check container status
docker-compose -f docker-compose.prod.yml ps
```

### Bare-Metal Deployments

```bash
# View logs
sudo journalctl -u family-calendar -f

# Check service status
sudo systemctl status family-calendar

# Restart service
sudo systemctl restart family-calendar

# Stop service
sudo systemctl stop family-calendar

# Start service
sudo systemctl start family-calendar

# Check Nginx status
sudo systemctl status nginx

# Restart Nginx
sudo systemctl restart nginx
```

## Troubleshooting

### Docker: Port Conflicts

If ports 8080/8443 are already in use, edit `docker-compose.prod.yml` and change the port mappings:

```yaml
ports:
  - "9080:80"   # Change 8080 to 9080
  - "9443:443"  # Change 8443 to 9443
```

### Database Locked Errors

If you see "database is locked" errors, ensure only one instance of the application is running:

```bash
# Docker
docker-compose -f docker-compose.prod.yml ps

# Bare-metal
sudo systemctl status family-calendar
```

### Permission Errors (Docker)

For Docker deployments, ensure proper ownership:

```bash
sudo chown -R 1000:1000 data logs ssl
```

### Service Won't Start (Bare-metal)

Check the logs for errors:

```bash
sudo journalctl -u family-calendar -xe
```

Common issues:
- Port 8000 already in use
- Python dependencies not installed
- Database migration issues

### Nginx Configuration Errors

Test nginx configuration:

```bash
sudo nginx -t
```

If errors, check `/etc/nginx/sites-available/family-calendar` for syntax issues.

## Getting Help

- Check logs for errors (see Management Commands above)
- Review [GitHub Issues](https://github.com/midij/family-calendar/issues)
- Verify prerequisites are installed correctly
- Ensure firewall rules allow required ports
