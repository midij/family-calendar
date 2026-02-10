# Telegram Bot Setup and Operations Guide

Complete guide for setting up and operating the Telegram bot for NLP event creation.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Local Development](#local-development)
4. [Testing](#testing)
5. [Production Deployment](#production-deployment)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts
- **Telegram Account**: For creating and managing the bot
- **OpenAI Account**: For NLP parsing (requires credits)
- **Cloudflare Account**: For tunnel service (free tier works)

### Required Tools
- Python 3.12+
- Virtual environment (venv)
- curl (for testing)
- Cloudflare Tunnel (`cloudflared`)

---

## Initial Setup

### 1. Create Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow prompts:
   - Bot name: "Family Calendar Bot" (or your choice)
   - Username: `YourFamilyCalendarBot` (must be unique)
4. **Save the bot token** (looks like: `123456:ABC-DEF1234ghIkl...`)

### 2. Get Telegram User IDs

Each family member needs to get their Telegram user ID:

1. Search for `@userinfobot` on Telegram
2. Send any message
3. Bot replies with your user ID (e.g., `8527503863`)
4. Collect all family members' IDs

### 3. Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. **Save the key** (starts with `sk-proj-...`)
4. **Add credits**: https://platform.openai.com/account/billing
   - Minimum: $5 (lasts for ~1,600 events)
   - Recommended: $10-20 for family use

### 4. Configure Environment

Create or edit `.env` file:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_ALLOWED_USER_IDS=123456789,987654321,333444555

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-actual-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Database
DATABASE_URL=sqlite:///./family_calendar.db
ENVIRONMENT=development
```

**Security Note**: Never commit `.env` to git. It's already in `.gitignore`.

---

## Local Development

### Setup Virtual Environment

```bash
# Navigate to project directory
cd family-calendar

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Start the Application

```bash
# Make sure venv is activated
source venv/bin/activate

# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Server will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Wall Display: http://localhost:8000/frontend/wall.html
- Admin: http://localhost:8000/frontend/admin.html

### Setup Cloudflare Tunnel (for webhook)

Telegram webhooks require HTTPS. Use Cloudflare Tunnel for local development:

#### Install Cloudflared

```bash
# macOS
brew install cloudflare/cloudflare/cloudflared

# Linux
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Windows
# Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation
```

#### Run Tunnel

In a **separate terminal** (keep it running):

```bash
cloudflared tunnel --url http://localhost:8000
```

You'll see output like:
```
Your quick Tunnel has been created! Visit it at:
https://random-words-here.trycloudflare.com
```

**Copy this URL** - you'll need it for the webhook.

### Configure Telegram Webhook

With both the server and tunnel running:

```bash
# Replace YOUR_TUNNEL_URL with the actual cloudflare URL
curl "http://localhost:8000/v1/telegram/setup?webhook_url=https://YOUR_TUNNEL_URL/v1/telegram/webhook"
```

Example:
```bash
curl "http://localhost:8000/v1/telegram/setup?webhook_url=https://random-words-here.trycloudflare.com/v1/telegram/webhook"
```

Expected response:
```json
{
  "status": "success",
  "webhook_url": "https://random-words-here.trycloudflare.com/v1/telegram/webhook",
  "pending_update_count": 0
}
```

### Verify Setup

```bash
# Check webhook status
curl http://localhost:8000/v1/telegram/webhook-info

# Or check directly from Telegram API
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

---

## Testing

### Test the Bot

1. **Start conversation**:
   - Open Telegram
   - Search for your bot
   - Click "Start" or send `/start`
   - You should get a help message

2. **Test simple event**:
   ```
   Soccer practice for Emma tomorrow at 4pm
   ```
   Expected: Confirmation message with ✅ and ❌ buttons

3. **Test recurring event**:
   ```
   Piano lessons every Tuesday at 4pm
   ```
   Expected: Confirmation showing "Repeats: Weekly on Tuesday"

4. **Confirm event**:
   - Click ✅ Confirm button
   - Expected: "Event created!" message
   - Check calendar at http://localhost:8000/frontend/wall.html

### Test Commands

```bash
# In Telegram, send these commands:
/start     # Shows help and welcome message
/help      # Shows usage examples

# Test messages:
"Dentist for Emma tomorrow 2pm"
"Family dinner this Friday 6pm at Luigi's"
"Swimming lessons every Monday and Wednesday 5pm"
```

### Monitor Logs

Watch the uvicorn terminal for real-time logs:
```
INFO: 91.108.5.139:0 - "POST /v1/telegram/webhook HTTP/1.1" 200 OK
```

### Test API Directly

```bash
# Test NLP parsing (requires OpenAI credits)
curl -X POST http://localhost:8000/v1/telegram/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "message_id": 1,
      "from": {"id": YOUR_USER_ID, "first_name": "Test"},
      "chat": {"id": YOUR_USER_ID},
      "text": "Soccer practice tomorrow 4pm"
    }
  }'
```

### Automated Tests

```bash
# Run test suite
pytest tests/test_telegram_integration.py -v

# Run with coverage
pytest tests/test_telegram_integration.py --cov=app/services
```

---

## Production Deployment

### Quick Reference: API Keys in Docker/Production

**❓ Where should I put API keys?**

| Method | Recommended | Why |
|--------|-------------|-----|
| `.env` file | ✅ YES | Secure, git-ignored, easy to manage |
| `docker-compose.yml` | ❌ NO | Would be committed to git (insecure) |
| `config.py` | ❌ NO | Would be committed to git (insecure) |
| System env vars | ✅ YES | Secure alternative to .env |

**📋 Deployment Workflow:**
```
1. Clone repo → 2. Create .env with API keys → 3. Run deploy script
```

**⚠️ Important**: The deploy script **cannot** be fully automated because API keys must be added manually for security.

---

### Option 1: Deploy with Docker

**IMPORTANT**: Docker reads API keys from `.env` file (NOT hardcoded in YAML).

#### Step 1: Prepare Server

```bash
# Clone repository on server
git clone https://github.com/midij/family-calendar.git
cd family-calendar
git checkout feature/telegram-nlp-events  # Or main after merge
```

#### Step 2: Create .env File (REQUIRED)

```bash
# Copy example file
cp .env.example .env

# Edit with your actual API keys
nano .env
```

**Add your credentials:**
```bash
TELEGRAM_BOT_TOKEN=your_actual_bot_token_from_botfather
TELEGRAM_ALLOWED_USER_IDS=123456789,987654321
OPENAI_API_KEY=sk-proj-your-actual-openai-key
OPENAI_MODEL=gpt-3.5-turbo
ENVIRONMENT=production
```

**Security Note**: The `.env` file is git-ignored and won't be committed.

#### Step 3: Deploy with Docker

```bash
# Docker Compose automatically reads from .env
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

The `docker-compose.prod.yml` already has this configured:
```yaml
environment:
  - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}     # ✅ Reads from .env
  - TELEGRAM_ALLOWED_USER_IDS=${TELEGRAM_ALLOWED_USER_IDS}
  - OPENAI_API_KEY=${OPENAI_API_KEY}
```

#### Step 4: Set Production Webhook

```bash
# Replace with your actual domain (HTTPS required)
curl "https://your-domain.com/v1/telegram/setup?webhook_url=https://your-domain.com/v1/telegram/webhook"

# Verify webhook is set
curl "https://your-domain.com/v1/telegram/webhook-info"
```

### Option 2: Deploy with Bare Metal (systemd)

#### Step 1: Get API Keys First

Before running deploy script, get your API keys:
1. Telegram bot token from @BotFather
2. User IDs from @userinfobot  
3. OpenAI API key from platform.openai.com

#### Step 2: Clone and Configure

```bash
# On your server
git clone https://github.com/midij/family-calendar.git
cd family-calendar
git checkout feature/telegram-nlp-events  # Or main after merge

# Create .env file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

**Add your credentials:**
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ALLOWED_USER_IDS=123456,789012
OPENAI_API_KEY=sk-proj-your-key
ENVIRONMENT=production
```

#### Step 3: Run Deploy Script

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment (automated from here)
./deploy.sh production
```

**What deploy.sh automates:**
- ✅ Installs system dependencies (Python, nginx, etc.)
- ✅ Sets up virtual environment
- ✅ Installs Python packages
- ✅ Configures systemd service
- ✅ Sets up nginx reverse proxy
- ✅ Configures firewall
- ✅ Starts services

**What you must do manually:**
- ❌ Create/edit `.env` with API keys (can't be automated for security)
- ❌ Set up SSL certificate (optional): `sudo certbot --nginx -d yourdomain.com`
- ❌ Set Telegram webhook (after deployment)

#### Step 4: Set Webhook

```bash
curl "https://your-domain.com/v1/telegram/setup?webhook_url=https://your-domain.com/v1/telegram/webhook"
```

### Option 3: Update Existing Deployment

If you already have the calendar deployed:

```bash
# SSH into your server
ssh user@your-server-ip

# Navigate to project
cd /opt/family-calendar  # Or wherever it's deployed

# Pull latest changes
git pull origin feature/telegram-nlp-events

# Update .env with new variables
nano .env
# Add: TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USER_IDS, OPENAI_API_KEY

# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart family-calendar  # For systemd
# OR
docker-compose -f docker-compose.prod.yml restart  # For Docker

# Set webhook
curl "https://your-domain.com/v1/telegram/setup?webhook_url=https://your-domain.com/v1/telegram/webhook"
```

---

## Troubleshooting

### Common Issues

#### 1. Bot Not Responding

**Check webhook status:**
```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

Look for:
- `pending_update_count`: Should be 0
- `last_error_message`: Should be null
- `url`: Should match your webhook URL

**Common fixes:**
- Verify webhook URL is HTTPS (not HTTP)
- Check if server is running: `curl https://your-domain.com/health`
- Restart cloudflared tunnel if using locally
- Check firewall allows incoming connections

#### 2. "Error 429: Insufficient Quota"

**Problem**: OpenAI API has no credits

**Fix:**
1. Go to https://platform.openai.com/account/billing
2. Add credits ($5 minimum)
3. Wait 1-2 minutes for activation
4. Retry sending message

#### 3. Wrong Timezone (Events 8 Hours Off)

**Problem**: Times are stored as UTC instead of Pacific

**Fix**: Already fixed in code (line 262-270 of `telegram.py`)
- Parses times as Pacific Time
- Converts to UTC for storage
- Frontend displays in local time

#### 4. "Unauthorized Access"

**Problem**: Your Telegram user ID is not in TELEGRAM_ALLOWED_USER_IDS

**Fix:**
1. Get your user ID from `@userinfobot`
2. Add to `.env`: `TELEGRAM_ALLOWED_USER_IDS=123456,YOUR_ID`
3. Restart server

#### 5. Webhook Returns 404

**Problem**: Tunnel URL is wrong or server not running

**Fix:**
- Check tunnel is running: Visit tunnel URL in browser
- Verify URL has `/v1/telegram/webhook` at the end
- Check server logs for incoming requests
- Try recreating tunnel (cloudflared generates new URLs each time)

#### 6. Ngrok Shows "ERR_NGROK_3200"

**Problem**: Ngrok free tier blocks webhooks with browser warning page

**Fix**: Use Cloudflare Tunnel instead (see setup above)

### Debug Mode

Enable detailed logging:

```python
# In app/main.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Logs

```bash
# Docker logs
docker-compose logs -f family-calendar

# Systemd logs
journalctl -u family-calendar -f

# Local development
# Watch the terminal running uvicorn
```

### Test Components Individually

```bash
# Test OpenAI API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"

# Test Telegram API
curl "https://api.telegram.org/bot<TOKEN>/getMe"

# Test local endpoint
curl http://localhost:8000/health
```

---

## Operational Notes

### Cost Management

**OpenAI Usage**:
- Monitor usage: https://platform.openai.com/usage
- Set spending limits: https://platform.openai.com/account/limits
- Average: $0.003 per event creation
- Budget: $10 = ~3,300 events

### Maintenance

**Weekly**:
- Check OpenAI credit balance
- Review error logs

**Monthly**:
- Review usage patterns
- Update dependencies if needed

### Security Best Practices

1. **Never commit `.env`** - Contains API keys
2. **Rotate API keys** if compromised
3. **Limit user access** - Only add trusted family members
4. **Monitor unusual activity** - Check logs for unauthorized attempts
5. **Keep dependencies updated** - Run `pip list --outdated` monthly

### Backup

Your `.env` file contains critical configuration:
```bash
# Backup .env file
cp .env .env.backup

# Store securely (outside git repo)
```

---

## Support

### Resources
- [Telegram Bot API Docs](https://core.telegram.org/bots/api)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

### Getting Help
1. Check this guide's troubleshooting section
2. Review server logs for error messages
3. Test components individually
4. Check API status pages:
   - Telegram: https://core.telegram.org/status
   - OpenAI: https://status.openai.com/
