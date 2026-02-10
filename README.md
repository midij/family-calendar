# Family Calendar

A wall-mounted calendar system for multi-child families to coordinate school activities, after-school programs, family events, and transportation.

## Features

- 📅 Weekly calendar view with color-coded events per child
- 🔄 Real-time updates via Server-Sent Events
- 🔁 Recurring events support (RRULE)
- 📥 CSV and ICS file import
- 🎨 Beautiful admin interface
- 📱 Responsive design optimized for wall displays

## Quick Start

### Local Development (Docker)

```bash
# Clone and start
git clone https://github.com/midij/family-calendar.git
cd family-calendar
docker-compose up -d

# Run migrations
docker exec -it family-calendar-app alembic upgrade head

# Access the app
# Wall Display: http://localhost:8000/frontend/wall.html
# Admin Interface: http://localhost:8000/frontend/admin.html
# API Docs: http://localhost:8000/docs
```

### Local Development (Without Docker)

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run migrations and start
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Deployment

### Docker Deployment (Recommended)

```bash
./deploy-docker.sh production
```

Access at `https://YOUR_SERVER_IP:8443/frontend/wall.html`

### Bare-Metal Deployment

**Option 1: Direct download**
```bash
curl -sSL https://raw.githubusercontent.com/midij/family-calendar/main/deploy.sh -o deploy.sh
chmod +x deploy.sh && ./deploy.sh production
```

**Option 2: Clone and deploy**
```bash
git clone https://github.com/midij/family-calendar.git
cd family-calendar
./deploy.sh production
```

Access at `http://YOUR_SERVER_IP/frontend/wall.html`

## Updating

### Docker
```bash
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec family-calendar alembic upgrade head
```

### Bare-Metal
```bash
./deploy.sh production  # Automatically pulls updates and preserves data
```

## Backup

```bash
./backup-data.sh
```

Backups stored in `~/family-calendar-backups/` (auto-cleanup after 30 days).

## Documentation

- [Detailed Deployment Guide](docs/DEPLOYMENT.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [Development Tasks](docs/DEV_TASKS.md)

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, SQLite
- **Frontend:** Vanilla JS, FullCalendar
- **Deployment:** Docker, Nginx, Systemd

## Project Structure

```
family-calendar/
├── app/                 # Backend API
├── frontend/            # Frontend files
├── data/                # SQLite database
├── deploy-docker.sh     # Docker deployment
├── deploy.sh            # Bare-metal deployment
└── backup-data.sh       # Backup script
```

## License

MIT
