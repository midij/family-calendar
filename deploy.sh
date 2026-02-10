#!/bin/bash

# Family Calendar Deployment Script
# Usage: ./deploy.sh [production|development]

set -e

ENVIRONMENT=${1:-production}
PROJECT_DIR="/opt/family-calendar"
SERVICE_NAME="family-calendar"
NGINX_SITE="family-calendar"

echo "🚀 Starting Family Calendar deployment..."
echo "Environment: $ENVIRONMENT"
echo "Project directory: $PROJECT_DIR"

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        echo "❌ This script should not be run as root for security reasons"
        echo "Please run as a regular user with sudo privileges"
        exit 1
    fi
}

# Function to install system dependencies
install_dependencies() {
    echo "📦 Installing system dependencies..."
    
    sudo apt update
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        nginx \
        git \
        curl \
        ufw \
        certbot \
        python3-certbot-nginx
    
    echo "✅ System dependencies installed"
}

# Function to setup application directory
setup_application() {
    echo "📁 Setting up application directory..."
    
    # Create directory if it doesn't exist
    sudo mkdir -p $PROJECT_DIR
    sudo chown $USER:$USER $PROJECT_DIR
    
    # Clone or update repository
    if [ -d "$PROJECT_DIR/.git" ]; then
        echo "🔄 Updating existing repository..."
        cd $PROJECT_DIR
        git pull origin main
    else
        echo "📥 Cloning repository..."
        git clone https://github.com/midij/family-calendar.git $PROJECT_DIR
        cd $PROJECT_DIR
    fi
    
    echo "✅ Application directory setup complete"
}

# Function to setup Python environment
setup_python_env() {
    echo "🐍 Setting up Python environment..."
    
    cd $PROJECT_DIR
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo "✅ Python environment setup complete"
}

# Function to setup database
setup_database() {
    echo "🗄️ Setting up database..."
    
    cd $PROJECT_DIR
    source venv/bin/activate
    
    # Run database migrations
    alembic upgrade head
    
    echo "✅ Database setup complete"
}

# Function to create production configuration
create_config() {
    echo "⚙️ Creating production configuration..."
    
    cd $PROJECT_DIR
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Production Environment
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=sqlite:///./family_calendar.db

# Security
SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=["https://yourdomain.com", "http://yourdomain.com"]

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/family-calendar/app.log
EOF
        echo "✅ Created .env configuration file"
    else
        echo "ℹ️ .env file already exists, skipping creation"
    fi
}

# Function to setup systemd service
setup_systemd_service() {
    echo "🔧 Setting up systemd service..."
    
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=Family Calendar API Server
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP \$MAINPID
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
ReadWritePaths=$PROJECT_DIR

[Install]
WantedBy=multi-user.target
EOF
    
    # Set proper ownership
    sudo chown -R www-data:www-data $PROJECT_DIR
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    
    echo "✅ Systemd service setup complete"
}

# Function to setup Nginx
setup_nginx() {
    echo "🌐 Setting up Nginx..."
    
    # Create Nginx configuration
    sudo tee /etc/nginx/sites-available/$NGINX_SITE > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss;
    
    # Static files (frontend)
    location /frontend/ {
        alias /opt/family-calendar/frontend/;
        expires 1h;
        add_header Cache-Control "public, immutable";
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
EOF
    
    # Enable the site
    sudo ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
    
    # Remove default site
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test configuration
    sudo nginx -t
    
    echo "✅ Nginx setup complete"
}

# Function to setup firewall
setup_firewall() {
    echo "🔥 Setting up firewall..."
    
    sudo ufw --force enable
    sudo ufw allow 22/tcp    # SSH
    sudo ufw allow 80/tcp    # HTTP
    sudo ufw allow 443/tcp   # HTTPS
    
    echo "✅ Firewall setup complete"
}

# Function to setup logging
setup_logging() {
    echo "📝 Setting up logging..."
    
    # Create log directory
    sudo mkdir -p /var/log/family-calendar
    sudo chown www-data:www-data /var/log/family-calendar
    
    # Configure logrotate
    sudo tee /etc/logrotate.d/family-calendar > /dev/null << EOF
/var/log/family-calendar/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF
    
    echo "✅ Logging setup complete"
}

# Function to start services
start_services() {
    echo "🚀 Starting services..."
    
    # Start and enable services
    sudo systemctl start $SERVICE_NAME
    sudo systemctl restart nginx
    
    # Check service status
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        echo "✅ Family Calendar service is running"
    else
        echo "❌ Family Calendar service failed to start"
        sudo systemctl status $SERVICE_NAME
        exit 1
    fi
    
    if sudo systemctl is-active --quiet nginx; then
        echo "✅ Nginx service is running"
    else
        echo "❌ Nginx service failed to start"
        sudo systemctl status nginx
        exit 1
    fi
}

# Function to run health check
health_check() {
    echo "🏥 Running health check..."
    
    sleep 5  # Wait for service to start
    
    if curl -f -s http://localhost:8000/health > /dev/null; then
        echo "✅ Health check passed"
    else
        echo "❌ Health check failed"
        echo "Service logs:"
        sudo journalctl -u $SERVICE_NAME -n 20
        exit 1
    fi
}

# Function to display deployment info
display_info() {
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "📱 Access URLs:"
    echo "  Wall Display: http://$(curl -s ifconfig.me)/frontend/wall.html"
    echo "  Admin Interface: http://$(curl -s ifconfig.me)/frontend/admin.html"
    echo "  Health Check: http://$(curl -s ifconfig.me)/health"
    echo ""
    echo "🔧 Management Commands:"
    echo "  Service status: sudo systemctl status $SERVICE_NAME"
    echo "  View logs: sudo journalctl -u $SERVICE_NAME -f"
    echo "  Restart service: sudo systemctl restart $SERVICE_NAME"
    echo "  Nginx status: sudo systemctl status nginx"
    echo ""
    echo "📋 Next Steps:"
    echo "  1. Configure your domain name in /etc/nginx/sites-available/$NGINX_SITE"
    echo "  2. Set up SSL certificates with: sudo certbot --nginx -d yourdomain.com"
    echo "  3. Update CORS_ORIGINS in $PROJECT_DIR/.env with your domain"
    echo "  4. Restart the service: sudo systemctl restart $SERVICE_NAME"
    echo ""
}

# Main deployment flow
main() {
    check_root
    install_dependencies
    setup_application
    setup_python_env
    setup_database
    create_config
    setup_systemd_service
    setup_nginx
    setup_firewall
    setup_logging
    start_services
    health_check
    display_info
}

# Run main function
main "$@"
