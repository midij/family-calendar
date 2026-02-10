# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-02-10

### Added - Telegram Bot NLP Event Creation

#### Features
- **Telegram Bot Integration**: Create calendar events via natural language messages
- **OpenAI NLP Parsing**: Intelligent event parsing using GPT-3.5-turbo
  - Automatically extracts: title, date, time, location, kids, category
  - Supports recurring events with RRULE generation
  - Handles complex patterns: "every Tuesday", "first Friday of each month"
- **Interactive Confirmations**: Preview events before creation with inline buttons
- **Timezone Support**: Proper Pacific Time (PST/PDT) handling with UTC storage
- **User Authorization**: Environment-based access control via Telegram user IDs

#### New Files
- `app/services/nlp_service.py` - OpenAI NLP parsing service
- `app/services/telegram_service.py` - Telegram bot interaction service
- `app/api/v1/endpoints/telegram.py` - Webhook endpoint for Telegram updates
- `tests/test_telegram_integration.py` - Comprehensive test suite
- `.env.example` - Environment configuration template
- `docs/TELEGRAM_BOT_SETUP.md` - Setup and operational guide

#### Modified Files
- `requirements.txt` - Added dependencies:
  - `python-telegram-bot==20.7`
  - `openai==1.10.0`
  - `python-dotenv==1.0.0`
  - `httpx~=0.25.2` (updated for compatibility)
- `app/config.py` - Added Telegram and OpenAI settings
- `app/api/v1/api.py` - Registered telegram router
- `app/schemas/event.py` - Added "telegram" as valid event source
- `docker-compose.yml` - Added Telegram/OpenAI environment variables
- `docker-compose.prod.yml` - Added Telegram/OpenAI environment variables
- `README.md` - Added Telegram bot feature documentation

#### Technical Details
- **NLP Features**:
  - Natural language parsing with OpenAI GPT-3.5-turbo
  - RRULE generation for recurring events (RFC5545 compliant)
  - RRULE validation using existing RRuleService
  - Human-readable RRULE conversion
  - Kid name validation and fuzzy matching
  - Confidence scoring (high/medium/low)

- **Timezone Handling**:
  - Input times parsed as America/Los_Angeles (Pacific Time)
  - Automatic conversion to UTC for database storage
  - Frontend displays in local timezone

- **Security**:
  - User authorization via TELEGRAM_ALLOWED_USER_IDS environment variable
  - Unauthorized users receive informative rejection messages
  - Environment variables protected by .gitignore

- **Error Handling**:
  - Graceful OpenAI API error handling
  - User-friendly error messages via Telegram
  - Comprehensive logging for debugging

#### Example Usage
```
User: "Soccer practice for Emma tomorrow at 4pm"
Bot: Shows confirmation with parsed details
User: Clicks ✅ Confirm
Bot: Creates event in calendar
```

#### Cost Estimation
- **Telegram**: Free, unlimited messages
- **OpenAI GPT-3.5-turbo**: ~$0.003 per event
- **Monthly (200 events)**: ~$0.60 in API costs

#### Breaking Changes
None - all changes are additive

#### Migration Notes
- Requires OpenAI API key with available credits
- Requires Telegram bot token from @BotFather
- Requires user IDs added to TELEGRAM_ALLOWED_USER_IDS
- No database migrations needed

#### Known Issues
- Ngrok free tier blocks webhooks (use Cloudflare Tunnel instead)
- OpenAI quota errors show generic "insufficient quota" message
- Timezone is hardcoded to Pacific (future: make configurable per user)

#### Future Enhancements
- WhatsApp integration (after business verification)
- Multi-timezone support per user
- Event editing via Telegram
- Event deletion via Telegram
- List events via Telegram
- Recurring event exceptions handling
- Voice message support
- Photo attachment support for event details
