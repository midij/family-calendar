#!/bin/bash

# Family Calendar - Docker-Only Deployment Script
# This script deploys the application using Docker without making any system changes
# Usage: ./deploy-docker.sh [production|development]

set -e

ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.yml"

if [ "$ENVIRONMENT" = "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

echo "🐳 Starting Family Calendar Docker deployment..."
echo "Environment: $ENVIRONMENT"
echo "Compose file: $COMPOSE_FILE"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "   sudo sh get-docker.sh"
    echo "   sudo usermod -aG docker \$USER"
    echo "   Then log out and back in."
    exit 1
fi

# Check Docker permissions
if ! docker ps &> /dev/null; then
    echo "❌ Docker permission denied. Please fix Docker permissions:"
    echo "   sudo usermod -aG docker \$USER"
    echo "   Then log out and back in, or run: newgrp docker"
    echo ""
    echo "Alternatively, you can run this script with sudo:"
    echo "   sudo ./deploy-docker.sh $ENVIRONMENT"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data logs ssl

# Set proper permissions for data directory
echo "🔐 Setting proper permissions..."
chmod 755 data logs ssl
# Set ownership to the user ID that will run in the container
chown -R 1000:1000 data logs ssl

# Create self-signed SSL certificate for development (if not exists)
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
    echo "🔐 Creating self-signed SSL certificate..."
    openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    echo "✅ SSL certificate created"
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down 2>/dev/null || true

# Force remove any problematic containers
echo "🧹 Cleaning up any problematic containers..."
docker container prune -f 2>/dev/null || true

# Build and start containers
echo "🏗️ Building and starting containers..."
# Use a specific user ID to avoid root user issues
export USER_ID=${USER_ID:-1000}
export GROUP_ID=${GROUP_ID:-1000}
docker-compose -f $COMPOSE_FILE up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose -f $COMPOSE_FILE exec family-calendar alembic upgrade head

# Seed sample data (optional)
read -p "🌱 Do you want to seed sample data? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🌱 Seeding sample data..."
    docker-compose -f $COMPOSE_FILE exec family-calendar python seed_data.py
fi

# Health check (skip for production)
if [ "$ENVIRONMENT" = "development" ]; then
    echo "🏥 Running health check..."
    sleep 5
    
    # Use ports 8080/8443 to avoid conflicts with other services
    echo "🔌 Using ports 8080 (HTTP) and 8443 (HTTPS) to avoid port conflicts"
    HEALTH_URL_HTTP="http://localhost:8080/health"
    HEALTH_URL_HTTPS="https://localhost:8443/health"
    
    if curl -f -s -k $HEALTH_URL_HTTPS > /dev/null 2>&1; then
        echo "✅ Health check passed (HTTPS on port 8443)"
    elif curl -f -s $HEALTH_URL_HTTP > /dev/null 2>&1; then
        echo "✅ Health check passed (HTTP on port 8080)"
    else
        echo "❌ Health check failed"
        echo "Container logs:"
        docker-compose -f $COMPOSE_FILE logs --tail=20
        exit 1
    fi
else
    echo "⏭️  Skipping health check for production deployment"
    echo "💡 You can manually test the application after deployment"
fi

# Display deployment info
echo ""
echo "🎉 Docker deployment completed successfully!"
echo ""
echo "📱 Access URLs:"
echo "  Wall Display: https://localhost:8443/frontend/wall.html"
echo "  Admin Interface: https://localhost:8443/frontend/admin.html"
echo "  Health Check: https://localhost:8443/health"
echo ""
echo "💡 For production deployments:"
echo "   Replace 'localhost' with your server's IP address or hostname"
echo "   Example: https://192.168.1.142:8443/frontend/wall.html"
echo ""
echo "🔧 Management Commands:"
echo "  View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "  Stop services: docker-compose -f $COMPOSE_FILE down"
echo "  Restart services: docker-compose -f $COMPOSE_FILE restart"
echo "  Update application: docker-compose -f $COMPOSE_FILE up -d --build"
echo ""
echo "📋 Container Status:"
docker-compose -f $COMPOSE_FILE ps
echo ""
echo "💡 Note: This deployment uses self-signed SSL certificates."
echo "   For production, replace ssl/cert.pem and ssl/key.pem with real certificates."
echo ""
echo "💾 Data Backup Setup:"
echo "   Manual backup: ./backup-data.sh"
echo "   Daily automated backup: Add to crontab:"
echo "   0 2 * * * cd $PWD && ./backup-data.sh >> ~/family-calendar-backups/backup.log 2>&1"
echo "   Backup location: ~/family-calendar-backups/"
echo ""
