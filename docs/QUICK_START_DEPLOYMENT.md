# Quick Start Deployment Guide

This guide provides the fastest way to deploy your Family Calendar system using Docker.

## Prerequisites

- Linux server with Docker support
- Basic knowledge of Linux command line
- 5-10 minutes of setup time

## Quick Docker Deployment

### Step 1: Install Docker (if not already installed)

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in to apply group changes
```

### Step 2: Deploy Family Calendar

```bash
# Clone the repository
git clone https://github.com/your-username/family-calendar.git
cd family-calendar

# Run the automated deployment script
chmod +x deploy-docker.sh
./deploy-docker.sh production
```

The script will automatically:
- Create necessary directories (`data`, `logs`, `ssl`)
- Generate self-signed SSL certificates
- Build and start Docker containers (app + nginx only)
- Run database migrations (SQLite - no database server needed)
- Set up health checks
- Display access URLs

### Step 3: Access Your Calendar

After deployment, access your calendar at:
- **Wall Display**: `https://localhost/frontend/wall.html`
- **Admin Interface**: `https://localhost/frontend/admin.html`
- **Health Check**: `https://localhost/health`

## Manual Docker Deployment (Alternative)

If you prefer to run the steps manually:

```bash
# Clone repository
git clone https://github.com/your-username/family-calendar.git
cd family-calendar

# Create necessary directories
mkdir -p data logs ssl

# Create self-signed SSL certificate
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations (SQLite - no database server needed)
docker-compose -f docker-compose.prod.yml exec family-calendar alembic upgrade head

# Seed sample data (optional)
docker-compose -f docker-compose.prod.yml exec family-calendar python seed_data.py
```

### Access Your Application
- **Wall Display**: `https://localhost/frontend/wall.html`
- **Admin Interface**: `https://localhost/frontend/admin.html`
- **Health Check**: `https://localhost/health`

## Post-Deployment Configuration

### Configure Domain (Optional)

If you have a domain name, edit `nginx/sites-available/family-calendar.conf`:

```nginx
server_name yourdomain.com www.yourdomain.com;
```

### Set up Real SSL Certificates (Optional)

Replace the self-signed certificates with real certificates:

```bash
# Copy your SSL certificates
cp your-cert.pem ssl/cert.pem
cp your-key.pem ssl/key.pem

# Restart containers
docker-compose -f docker-compose.prod.yml restart
```

### Update CORS Settings (Optional)

Edit environment variables in `docker-compose.prod.yml`:

```yaml
environment:
  - CORS_ORIGINS=["https://yourdomain.com", "http://yourdomain.com"]
```

## Management Commands

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Update application
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build

# Stop all services
docker-compose -f docker-compose.prod.yml down
```

## Access Your Calendar

### Wall Display (Tablet)
- **URL**: `https://localhost/frontend/wall.html` (or your domain)
- **Purpose**: Full-screen calendar for wall-mounted tablets
- **Features**: Real-time updates, week navigation, kid color coding

### Admin Interface (Phone/Computer)
- **URL**: `https://localhost/frontend/admin.html` (or your domain)
- **Purpose**: Manage events and kids
- **Features**: Create/edit events, manage kids, import/export data

## Troubleshooting

### Common Issues

**Containers won't start:**
```bash
# Check container logs
docker-compose -f docker-compose.prod.yml logs

# Check if ports are in use
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443

# Restart containers
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

**SSL certificate issues:**
```bash
# Check certificate files
ls -la ssl/

# Regenerate self-signed certificate
rm ssl/cert.pem ssl/key.pem
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

**Health check fails:**
```bash
# Test health endpoint
curl -k https://localhost/health

# Check container status
docker-compose -f docker-compose.prod.yml ps
```

## Security Checklist

- [ ] SSL certificate installed (replace self-signed for production)
- [ ] Firewall configured (ports 22, 80, 443)
- [ ] Regular container updates
- [ ] Application updates scheduled

## Performance Tuning

**Increase Workers:**
Edit `docker-compose.prod.yml`:
```yaml
environment:
  - WORKERS=8
```

**Enable Nginx Caching:**
The Nginx configuration already includes caching for static files.

## Support

For issues or questions:

1. Check container logs: `docker-compose -f docker-compose.prod.yml logs -f`
2. Test health endpoint: `curl -k https://localhost/health`
3. Check container status: `docker-compose -f docker-compose.prod.yml ps`
4. Check the full deployment guide: `docs/DEPLOYMENT.md`

Your Family Calendar is now ready for production use! 🎉

## Summary

This quick start guide provides a **fast, safe Docker deployment** that:
- ✅ Requires zero system changes
- ✅ Provides complete isolation from other applications
- ✅ Can be easily removed with `docker-compose down`
- ✅ Includes SSL, Nginx, and health checks
- ✅ Works on any system with Docker

For more detailed configuration options, see the full `docs/DEPLOYMENT.md` guide.
