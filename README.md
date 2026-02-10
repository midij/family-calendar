# Family Calendar

A wall-mounted calendar system designed for multi-child families to coordinate school activities, after-school programs, family events, and transportation arrangements.

## Features

- Weekly calendar view (Monday-Sunday)
- Child-specific event tracking with color coding
- Recurring event support (RRULE)
- Real-time updates via Server-Sent Events
- CSV and ICS file import capabilities
- Responsive design for wall mounting
- Beautiful admin interface for event management

## Table of Contents

- [Running Locally](#running-locally)
- [Deploying to a Server](#deploying-to-a-server)
- [Updating an Existing Deployment](#updating-an-existing-deployment)
- [Data Backup and Restore](#data-backup-and-restore)
- [Project Structure](#project-structure)

## Running Locally

### Prerequisites

- Docker and Docker Compose
- Git

### Quick Start (Development Mode)

1. **Clone the repository:**

```bash
git clone <repository-url>
cd family-calendar
```

2. **Start the development server:**

```bash
docker-compose up -d
```

3. **Run database migrations:**

```bash
docker exec -it family-calendar-app alembic upgrade head
```

4. **Access the application:**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

The development setup uses hot-reload, so any code changes will automatically restart the server.

### Alternative: Local Python Environment

If you prefer to run without Docker:

1. **Create a virtual environment:**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Run database migrations:**

```bash
alembic upgrade head
```

4. **Start the application:**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Deploying to a Server

There are two deployment options: **Docker deployment** (recommended) or **bare-metal deployment**.

### Option 1: Docker Deployment (Recommended)

This is the easiest and most reliable method. It uses containerization without modifying your system.

**Prerequisites:**
- Ubuntu/Debian server
- Docker and Docker Compose installed
- Ports 8080 and 8443 available

**Deploy:**

```bash
# Clone the repository
git clone <repository-url>
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

**Access your application:**
- Wall Display: `https://YOUR_SERVER_IP:8443/frontend/wall.html`
- Admin Interface: `https://YOUR_SERVER_IP:8443/frontend/admin.html`
- Health Check: `https://YOUR_SERVER_IP:8443/health`

**Note:** The deployment uses self-signed SSL certificates. For production, replace `ssl/cert.pem` and `ssl/key.pem` with real certificates from Let's Encrypt or your certificate provider.

### Option 2: Bare-Metal Deployment

This method installs everything directly on your server with systemd and Nginx. It's ideal if you prefer traditional server setup or need more control over the system configuration.

**Prerequisites:**
- Ubuntu/Debian server
- Sudo privileges
- Ports 80 and 443 available

**Deploy (Method 1 - Direct download):**

```bash
# Download the script
curl -sSL https://raw.githubusercontent.com/midij/family-calendar/main/deploy.sh -o deploy.sh

# Make executable and run
chmod +x deploy.sh && ./deploy.sh production
```

**Deploy (Method 2 - Clone repository):**

```bash
# Clone the repository
git clone <repository-url>
cd family-calendar

# Run the deployment script
./deploy.sh production
```

The script will automatically:
- Install system dependencies (Python, Nginx, UFW, Certbot)
- Create `/opt/family-calendar` directory
- Clone or update the repository (includes `git pull` for updates!)
- Create Python virtual environment
- Install Python dependencies
- Run database migrations
- Create and start systemd service
- Configure Nginx as reverse proxy
- Set up firewall rules
- Configure logging and log rotation

**Access your application:**
- Wall Display: `http://YOUR_SERVER_IP/frontend/wall.html`
- Admin Interface: `http://YOUR_SERVER_IP/frontend/admin.html`

**Next steps for production:**
1. Configure your domain in `/etc/nginx/sites-available/family-calendar`
2. Set up SSL: `sudo certbot --nginx -d yourdomain.com`
3. Update CORS settings in `/opt/family-calendar/.env`

**For updates:** Simply run `./deploy.sh production` again - it will automatically pull the latest code and update everything while preserving your database!

## Updating an Existing Deployment

When you have new changes from the repository and want to update your deployed application **without losing data**, follow these steps:

### For Docker Deployments

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

### For Bare-Metal Deployments

The easiest way is to simply re-run the deployment script - it handles everything automatically:

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

**Alternative manual method:**

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

## Data Backup and Restore

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

## Project Structure

```
family-calendar/
├── app/                      # Backend application
│   ├── api/                  # API endpoints
│   ├── models/               # Database models
│   ├── schemas/              # Pydantic schemas
│   └── main.py               # FastAPI application
├── frontend/                 # Frontend HTML/CSS/JS
│   ├── wall.html             # Wall display view
│   └── admin.html            # Admin interface
├── data/                     # Database storage (created on deployment)
├── logs/                     # Application logs (created on deployment)
├── ssl/                      # SSL certificates (created on deployment)
├── nginx/                    # Nginx configuration
├── docker-compose.yml        # Development Docker setup
├── docker-compose.prod.yml   # Production Docker setup
├── Dockerfile                # Development Dockerfile
├── Dockerfile.prod           # Production Dockerfile
├── deploy-docker.sh          # Docker deployment script
├── deploy.sh                 # Bare-metal deployment script
├── backup-data.sh            # Database backup script
└── requirements.txt          # Python dependencies
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

### Docker: Port conflicts

If ports 8080/8443 are already in use, edit `docker-compose.prod.yml` and change the port mappings:

```yaml
ports:
  - "9080:80"   # Change 8080 to 9080
  - "9443:443"  # Change 8443 to 9443
```

### Database locked errors

If you see "database is locked" errors, ensure only one instance of the application is running.

### Permission errors

For Docker deployments, ensure proper ownership:

```bash
sudo chown -R 1000:1000 data logs ssl
```

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation with Swagger UI.

## License

MIT 