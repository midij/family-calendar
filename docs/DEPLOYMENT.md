# Family Calendar - Production Deployment Guide

This guide covers deploying the Family Calendar system to a production server so that wall devices and phones can access the HTML interfaces.

## Table of Contents
1. [Server Requirements](#server-requirements)
2. [Quick Start Deployment](#quick-start-deployment)
3. [Detailed Deployment Steps](#detailed-deployment-steps)
4. [Production Configuration](#production-configuration)
5. [Nginx Configuration](#nginx-configuration)
6. [Systemd Service Setup](#systemd-service-setup)
7. [SSL/HTTPS Setup](#sslhttps-setup)
8. [Monitoring & Logging](#monitoring--logging)
9. [Troubleshooting](#troubleshooting)

## Server Requirements

### Minimum Requirements
- **OS**: Ubuntu 20.04+ or CentOS 8+ (Linux recommended)
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 10GB minimum
- **CPU**: 2 cores minimum
- **Network**: Static IP address or domain name

### Software Dependencies
- Python 3.8+
- Nginx (for reverse proxy and static file serving)
- PostgreSQL (optional, SQLite works for small deployments)
- Docker (optional, for containerized deployment)

## Quick Start Deployment

### Option 1: Direct Python Deployment (Recommended for small setups)

```bash
# 1. Clone the repository
git clone https://github.com/your-username/family-calendar.git
cd family-calendar

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database
alembic upgrade head

# 5. Start the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Option 2: Docker Deployment (Recommended for production)

```bash
# 1. Clone and build
git clone https://github.com/your-username/family-calendar.git
cd family-calendar
docker build -t family-calendar .

# 2. Run with Docker Compose
docker-compose up -d
```

## Detailed Deployment Steps

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx git -y

# Install Node.js (if needed for frontend builds)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Step 2: Application Deployment

```bash
# Create application directory
sudo mkdir -p /opt/family-calendar
sudo chown $USER:$USER /opt/family-calendar
cd /opt/family-calendar

# Clone repository
git clone https://github.com/your-username/family-calendar.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
alembic upgrade head

# Create production configuration
cp .env.example .env
# Edit .env with production settings
```

### Step 3: Production Configuration

Create `/opt/family-calendar/.env`:

```env
# Production Environment
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=sqlite:///./family_calendar.db
# For PostgreSQL: DATABASE_URL=postgresql://user:password@localhost/family_calendar

# Security
SECRET_KEY=your-super-secret-key-here
CORS_ORIGINS=["https://yourdomain.com", "http://yourdomain.com"]

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/family-calendar/app.log
```

## Production Configuration

### Application Configuration

Create `/opt/family-calendar/app/config.py`:

```python
import os
from typing import List

class Settings:
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./family_calendar.db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "4"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "/var/log/family-calendar/app.log")

settings = Settings()
```

## Nginx Configuration

### Create Nginx Configuration

Create `/etc/nginx/sites-available/family-calendar`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss;
    
    # Static files (frontend HTML, CSS, JS)
    location /frontend/ {
        alias /opt/family-calendar/frontend/;
        expires 1h;
        add_header Cache-Control "public, immutable";
        
        # Security for HTML files
        location ~* \.html$ {
            add_header X-Frame-Options "SAMEORIGIN";
            add_header X-Content-Type-Options "nosniff";
        }
    }
    
    # API endpoints
    location /v1/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Root redirect to wall display
    location = / {
        return 301 /frontend/wall.html;
    }
    
    # Admin interface
    location = /admin {
        return 301 /frontend/admin.html;
    }
}
```

### Enable Nginx Configuration

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/family-calendar /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

## Systemd Service Setup

### Create Systemd Service

Create `/etc/systemd/system/family-calendar.service`:

```ini
[Unit]
Description=Family Calendar API Server
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/family-calendar
Environment=PATH=/opt/family-calendar/venv/bin
ExecStart=/opt/family-calendar/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=family-calendar

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/family-calendar

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable family-calendar

# Start service
sudo systemctl start family-calendar

# Check status
sudo systemctl status family-calendar

# View logs
sudo journalctl -u family-calendar -f
```

## SSL/HTTPS Setup

### Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## Monitoring & Logging

### Application Logging

Create log directory and configure logging:

```bash
# Create log directory
sudo mkdir -p /var/log/family-calendar
sudo chown www-data:www-data /var/log/family-calendar

# Configure logrotate
sudo tee /etc/logrotate.d/family-calendar << EOF
/var/log/family-calendar/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload family-calendar
    endscript
}
EOF
```

### Health Monitoring

The application includes health check endpoints:

- `GET /health` - Basic health check
- `GET /v1/events/version` - API version and last update info

### Monitoring Script

Create `/opt/family-calendar/monitor.sh`:

```bash
#!/bin/bash
# Health check script

HEALTH_URL="http://localhost:8000/health"
LOG_FILE="/var/log/family-calendar/health.log"

# Check if service is running
if ! systemctl is-active --quiet family-calendar; then
    echo "$(date): Service is not running, restarting..." >> $LOG_FILE
    systemctl restart family-calendar
    exit 1
fi

# Check health endpoint
if ! curl -f -s $HEALTH_URL > /dev/null; then
    echo "$(date): Health check failed, restarting..." >> $LOG_FILE
    systemctl restart family-calendar
    exit 1
fi

echo "$(date): Health check passed" >> $LOG_FILE
```

```bash
# Make executable
chmod +x /opt/family-calendar/monitor.sh

# Add to crontab (check every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/family-calendar/monitor.sh") | crontab -
```

## Access URLs

After deployment, your devices can access:

### Wall Display (Tablet)
- **URL**: `https://yourdomain.com/frontend/wall.html`
- **Purpose**: Full-screen calendar display for wall-mounted tablets

### Admin Interface (Phone/Computer)
- **URL**: `https://yourdomain.com/frontend/admin.html`
- **Purpose**: Event and kid management interface

### API Endpoints
- **Base URL**: `https://yourdomain.com/v1/`
- **Health Check**: `https://yourdomain.com/health`

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo journalctl -u family-calendar -n 50
   ```

2. **Nginx 502 Bad Gateway**
   - Check if the application is running: `sudo systemctl status family-calendar`
   - Check port 8000: `sudo netstat -tlnp | grep 8000`

3. **Static files not loading**
   - Check Nginx configuration: `sudo nginx -t`
   - Verify file permissions: `ls -la /opt/family-calendar/frontend/`

4. **Database issues**
   ```bash
   cd /opt/family-calendar
   source venv/bin/activate
   alembic current
   alembic upgrade head
   ```

### Performance Tuning

1. **Increase worker processes** (in systemd service):
   ```
   ExecStart=/opt/family-calendar/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 8
   ```

2. **Enable Nginx caching** for static files:
   ```nginx
   location /frontend/ {
       alias /opt/family-calendar/frontend/;
       expires 1d;
       add_header Cache-Control "public, immutable";
   }
   ```

3. **Database optimization** (for PostgreSQL):
   ```sql
   -- Add indexes for better performance
   CREATE INDEX idx_events_start_utc ON events(start_utc);
   CREATE INDEX idx_events_kid_ids ON events USING GIN(kid_ids);
   ```

## Security Considerations

1. **Firewall Configuration**
   ```bash
   sudo ufw allow 22/tcp    # SSH
   sudo ufw allow 80/tcp    # HTTP
   sudo ufw allow 443/tcp   # HTTPS
   sudo ufw enable
   ```

2. **Regular Updates**
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade -y
   
   # Update application
   cd /opt/family-calendar
   git pull origin main
   source venv/bin/activate
   pip install -r requirements.txt
   sudo systemctl restart family-calendar
   ```

3. **Backup Strategy**
   ```bash
   # Backup database
   cp /opt/family-calendar/family_calendar.db /backup/family_calendar_$(date +%Y%m%d).db
   
   # Backup configuration
   tar -czf /backup/family-calendar-config_$(date +%Y%m%d).tar.gz /opt/family-calendar/.env /etc/nginx/sites-available/family-calendar
   ```

This deployment guide provides a complete production setup for your Family Calendar system. The wall device and phones will be able to access the HTML interfaces through the configured domain name with proper SSL security.
