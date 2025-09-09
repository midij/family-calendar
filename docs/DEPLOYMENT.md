# Family Calendar - Production Deployment Guide

This guide covers deploying the Family Calendar system to a production server so that wall devices and phones can access the HTML interfaces.

## Table of Contents
1. [Deployment Options](#deployment-options)
2. [Server Requirements](#server-requirements)
3. [Docker Deployment](#docker-deployment)
4. [SSL/HTTPS Setup](#sslhttps-setup)
5. [Monitoring & Logging](#monitoring--logging)
6. [Troubleshooting](#troubleshooting)

## Why Docker Deployment?

Docker deployment is the recommended approach because it provides:

- ✅ **Zero system changes** - No global packages or services installed
- ✅ **Complete isolation** - Won't affect other applications on your server
- ✅ **Easy cleanup** - Just `docker-compose down` to remove everything
- ✅ **Production-ready** - Includes Nginx, SSL, health checks, and monitoring
- ✅ **Portable** - Works on any system with Docker support
- ✅ **Consistent** - Same environment across development, staging, and production

## Server Requirements

### Minimum Requirements
- **OS**: Any Linux distribution with Docker support
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 10GB minimum
- **CPU**: 2 cores minimum
- **Network**: Static IP address or domain name

### Software Dependencies
- **Docker** (for containerized deployment)
- **Docker Compose** (for multi-container setup)
- **Git** (for cloning repository)

### Database
- **SQLite** (embedded database - no separate installation needed)
- **No database server required** - SQLite runs within the application container
- **No passwords or authentication** - Simple file-based database

## Docker Deployment

### Prerequisites
- Docker and Docker Compose installed
- Ports 80 and 443 available (or configure different ports)
- Git installed

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-username/family-calendar.git
cd family-calendar

# 2. Run Docker deployment script
chmod +x deploy-docker.sh
./deploy-docker.sh production
```

The deployment script will automatically:
- Create necessary directories (`data`, `logs`, `ssl`)
- Generate self-signed SSL certificates
- Build and start Docker containers (app + nginx only)
- Run database migrations (SQLite - no database server needed)
- Set up health checks
- Display access URLs and management commands

### Manual Docker Deployment

If you prefer to run the deployment steps manually:

```bash
# 1. Create necessary directories
mkdir -p data logs ssl

# 2. Create self-signed SSL certificate (for development)
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# 3. Start services
docker-compose -f docker-compose.prod.yml up -d

# 4. Run database migrations (SQLite - no database server needed)
docker-compose -f docker-compose.prod.yml exec family-calendar alembic upgrade head

# 5. Seed sample data (optional)
docker-compose -f docker-compose.prod.yml exec family-calendar python seed_data.py
```

### Access Your Application
- **Wall Display**: `https://localhost:8443/frontend/wall.html`
- **Admin Interface**: `https://localhost:8443/frontend/admin.html`
- **Health Check**: `https://localhost:8443/health`

### Management Commands
```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Update application
docker-compose -f docker-compose.prod.yml up -d --build

# Check container status
docker-compose -f docker-compose.prod.yml ps
```

## Alternative Deployment Options

If Docker is not available in your environment, you can use alternative deployment methods:

- **User-Space Deployment**: Run under a user account without system changes
- **System-Wide Deployment**: Traditional deployment with system packages (legacy)

For detailed instructions on these alternatives, see `docs/QUICK_START_DEPLOYMENT.md`.

## Docker Configuration

The Docker deployment includes pre-configured Nginx and application containers. The configuration files are located in:

- **Nginx Config**: `nginx/nginx.conf` and `nginx/sites-available/family-calendar.conf`
- **Docker Compose**: `docker-compose.prod.yml`
- **Application**: `Dockerfile.prod`

### Customizing Configuration

To modify the configuration:

1. **Edit Nginx settings**: Modify `nginx/sites-available/family-calendar.conf`
2. **Change environment variables**: Edit `docker-compose.prod.yml`
3. **Update SSL certificates**: Replace files in `ssl/` directory
4. **Restart containers**: `docker-compose -f docker-compose.prod.yml restart`

## SSL/HTTPS Setup

### For Docker Deployment

The Docker deployment includes self-signed SSL certificates for development. For production:

1. **Replace SSL certificates**:
   ```bash
   # Copy your SSL certificates
   cp your-cert.pem ssl/cert.pem
   cp your-key.pem ssl/key.pem
   
   # Restart containers
   docker-compose -f docker-compose.prod.yml restart
   ```

2. **Using Let's Encrypt** (if running on a domain):
   ```bash
   # Install Certbot
   sudo apt install certbot -y
   
   # Get SSL certificate
   sudo certbot certonly --standalone -d yourdomain.com
   
   # Copy certificates to ssl directory
   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
   sudo chown $USER:$USER ssl/cert.pem ssl/key.pem
   
   # Restart containers
   docker-compose -f docker-compose.prod.yml restart
   ```

## Monitoring & Logging

### Docker Logs

View application logs:
```bash
# View all container logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific container logs
docker-compose -f docker-compose.prod.yml logs -f family-calendar
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Health Monitoring

The application includes health check endpoints:

- `GET /health` - Basic health check
- `GET /v1/events/version` - API version and last update info

### Monitoring Script

Create a simple monitoring script:

```bash
#!/bin/bash
# Health check script for Docker deployment

HEALTH_URL="https://localhost/health"
LOG_FILE="./logs/health.log"

# Create logs directory if it doesn't exist
mkdir -p logs

# Check health endpoint
if curl -f -s -k $HEALTH_URL > /dev/null; then
    echo "$(date): Health check passed" >> $LOG_FILE
else
    echo "$(date): Health check failed, restarting containers..." >> $LOG_FILE
    docker-compose -f docker-compose.prod.yml restart
    exit 1
fi
```

```bash
# Make executable
chmod +x monitor.sh

# Add to crontab (check every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * cd /path/to/family-calendar && ./monitor.sh") | crontab -
```

## Access URLs

After Docker deployment, your devices can access:

### Wall Display (Tablet)
- **URL**: `https://localhost:8443/frontend/wall.html` (or your domain:8443)
- **Purpose**: Full-screen calendar display for wall-mounted tablets

### Admin Interface (Phone/Computer)
- **URL**: `https://localhost:8443/frontend/admin.html` (or your domain:8443)
- **Purpose**: Event and kid management interface

### API Endpoints
- **Base URL**: `https://localhost:8443/v1/` (or your domain:8443)
- **Health Check**: `https://localhost:8443/health` (or your domain:8443)

## Troubleshooting

### Docker Deployment Issues

1. **Containers won't start**
   ```bash
   # Check container logs
   docker-compose -f docker-compose.prod.yml logs
   
   # Check if ports are in use
   sudo netstat -tlnp | grep :80
   sudo netstat -tlnp | grep :443
   ```

2. **SSL certificate issues**
   ```bash
   # Check certificate files
   ls -la ssl/
   
   # Regenerate self-signed certificate
   rm ssl/cert.pem ssl/key.pem
   openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
   ```

3. **Database issues**
   ```bash
   # Check database file
   ls -la data/
   
   # Recreate database
   docker-compose -f docker-compose.prod.yml exec family-calendar alembic upgrade head
   ```

4. **Health check fails**
   ```bash
   # Test health endpoint directly
   curl -k https://localhost:8443/health
   
   # Check container status
   docker-compose -f docker-compose.prod.yml ps
   ```

### Performance Tuning

1. **Increase worker processes**:
   Edit `docker-compose.prod.yml`:
   ```yaml
   environment:
     - WORKERS=8
   ```

2. **Enable Nginx caching**:
   The Nginx configuration already includes caching for static files.

### Security Considerations

1. **Replace self-signed certificates** with real SSL certificates for production
2. **Configure firewall** to allow only necessary ports (22, 80, 443)
3. **Regular updates**:
   ```bash
   # Update application
   git pull origin main
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

4. **Backup strategy**:
   ```bash
   # Backup data directory
   tar -czf backup_$(date +%Y%m%d).tar.gz data/ ssl/ logs/
   ```

This deployment guide provides a complete Docker-based production setup for your Family Calendar system. The wall device and phones will be able to access the HTML interfaces through the configured domain name with proper SSL security.
