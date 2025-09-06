# Quick Start Deployment Guide

This guide provides the fastest way to deploy your Family Calendar system to a server.

## Prerequisites

- Ubuntu 20.04+ server with root/sudo access
- Domain name pointing to your server (optional, but recommended)
- Basic knowledge of Linux command line

## Option 1: Automated Deployment (Recommended)

### Step 1: Download and Run Deployment Script

```bash
# Download the deployment script
curl -O https://raw.githubusercontent.com/your-username/family-calendar/main/deploy.sh
chmod +x deploy.sh

# Run the deployment
./deploy.sh production
```

The script will automatically:
- Install all dependencies
- Set up the application
- Configure Nginx
- Set up systemd service
- Configure firewall
- Start all services

### Step 2: Access Your Calendar

After deployment, access your calendar at:
- **Wall Display**: `http://YOUR_SERVER_IP/frontend/wall.html`
- **Admin Interface**: `http://YOUR_SERVER_IP/frontend/admin.html`

## Option 2: Manual Deployment

### Step 1: Install Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx git curl
```

### Step 2: Clone and Setup Application

```bash
# Clone repository
git clone https://github.com/your-username/family-calendar.git /opt/family-calendar
cd /opt/family-calendar

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database
alembic upgrade head
```

### Step 3: Configure and Start Services

```bash
# Create systemd service
sudo cp docs/systemd/family-calendar.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable family-calendar
sudo systemctl start family-calendar

# Configure Nginx
sudo cp docs/nginx/family-calendar.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/family-calendar.conf /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
```

## Option 3: Docker Deployment

### Step 1: Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### Step 2: Deploy with Docker Compose

```bash
# Clone repository
git clone https://github.com/your-username/family-calendar.git
cd family-calendar

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

## Post-Deployment Configuration

### 1. Configure Domain (Optional)

Edit `/etc/nginx/sites-available/family-calendar` and replace `_` with your domain:

```nginx
server_name yourdomain.com www.yourdomain.com;
```

### 2. Set up SSL (Recommended)

```bash
sudo certbot --nginx -d yourdomain.com
```

### 3. Update CORS Settings

Edit `/opt/family-calendar/.env`:

```env
CORS_ORIGINS=["https://yourdomain.com", "http://yourdomain.com"]
```

### 4. Restart Services

```bash
sudo systemctl restart family-calendar
sudo systemctl restart nginx
```

## Access Your Calendar

### Wall Display (Tablet)
- **URL**: `https://yourdomain.com/frontend/wall.html`
- **Purpose**: Full-screen calendar for wall-mounted tablets
- **Features**: Real-time updates, week navigation, kid color coding

### Admin Interface (Phone/Computer)
- **URL**: `https://yourdomain.com/frontend/admin.html`
- **Purpose**: Manage events and kids
- **Features**: Create/edit events, manage kids, import/export data

## Management Commands

```bash
# Check service status
sudo systemctl status family-calendar

# View logs
sudo journalctl -u family-calendar -f

# Restart service
sudo systemctl restart family-calendar

# Update application
cd /opt/family-calendar
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart family-calendar
```

## Troubleshooting

### Service Won't Start
```bash
sudo journalctl -u family-calendar -n 50
```

### Nginx Issues
```bash
sudo nginx -t
sudo systemctl status nginx
```

### Port Already in Use
```bash
sudo netstat -tlnp | grep 8000
sudo lsof -i :8000
```

## Security Checklist

- [ ] Firewall configured (ports 22, 80, 443)
- [ ] SSL certificate installed
- [ ] Strong secret key in .env file
- [ ] Regular system updates
- [ ] Application updates scheduled

## Performance Tuning

### Increase Workers (for high traffic)
Edit `/etc/systemd/system/family-calendar.service`:
```
ExecStart=/opt/family-calendar/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 8
```

### Enable Nginx Caching
Add to Nginx configuration:
```nginx
location /frontend/ {
    alias /opt/family-calendar/frontend/;
    expires 1d;
    add_header Cache-Control "public, immutable";
}
```

## Support

For issues or questions:
1. Check the logs: `sudo journalctl -u family-calendar -f`
2. Verify configuration: `sudo nginx -t`
3. Test health endpoint: `curl http://localhost:8000/health`
4. Check the full deployment guide: `docs/DEPLOYMENT.md`

Your Family Calendar is now ready for production use! 🎉
