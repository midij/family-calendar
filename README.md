# Family Calendar

A wall-mounted calendar system for multi-child families to coordinate school activities, after-school programs, family events, and transportation.

## Features

- 📅 Weekly calendar view with color-coded events per child
- 🔄 Real-time updates via Server-Sent Events
- 🔁 Recurring events support (RRULE)
- 📥 CSV and ICS file import
- 🤖 Telegram bot with NLP for creating events via natural language
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
# Wall Display: http://localhost:8088/frontend/wall.html
# Admin Interface: http://localhost:8088/frontend/admin.html
# API Docs: http://localhost:8088/docs
```

### Local Development (Without Docker)

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure (for Telegram bot feature)
cp .env.example .env
nano .env  # Add Telegram and OpenAI API keys

# Run migrations and start
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**For Telegram bot testing (requires HTTPS):**
```bash
# In a separate terminal, run cloudflare tunnel
brew install cloudflare/cloudflare/cloudflared  # One-time install
cloudflared tunnel --url http://localhost:8088

# Copy the HTTPS URL and set webhook:
curl "http://localhost:8088/v1/telegram/setup?webhook_url=https://YOUR_TUNNEL_URL/v1/telegram/webhook"
```

## Deployment

**Important:** For Telegram bot feature, you must configure API keys before deploying.

### Docker Deployment (Recommended)

```bash
# Clone and configure
git clone https://github.com/midij/family-calendar.git
cd family-calendar
cp .env.example .env
nano .env  # Add Telegram and OpenAI API keys

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec family-calendar alembic upgrade head
```

Access at `https://YOUR_SERVER_IP:8443/frontend/wall.html`

### Bare-Metal Deployment

```bash
# Clone and configure
git clone https://github.com/midij/family-calendar.git
cd family-calendar
cp .env.example .env
nano .env  # Add Telegram and OpenAI API keys

# Deploy (installs dependencies, sets up nginx, systemd, etc.)
./deploy.sh production
```

Access at `http://YOUR_SERVER_IP/frontend/wall.html`

**Note:** See [`docs/TELEGRAM_BOT_SETUP.md`](docs/TELEGRAM_BOT_SETUP.md) for detailed deployment instructions.

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

## Telegram Bot (NLP Event Creation)

Create calendar events via natural language messages in Telegram!

**Examples:**
- "Soccer practice for Emma tomorrow at 4pm"
- "Piano lessons every Tuesday at 4pm"
- "Dentist checkup first Friday of each month 2pm"

**📖 Setup Guide:** See [`docs/TELEGRAM_BOT_SETUP.md`](docs/TELEGRAM_BOT_SETUP.md) for complete instructions on:
- Getting API keys (Telegram, OpenAI)
- Local testing setup
- Production deployment
- Troubleshooting

## Documentation

- [Detailed Deployment Guide](docs/DEPLOYMENT.md)
- [API Documentation](http://localhost:8088/docs) (when running)
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
