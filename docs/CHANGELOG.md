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

### Fixed - 2026-02-10

#### Bug: Recurring Events Not Showing in Calendar View
- **Issue**: When creating recurring events via Telegram (e.g., "every Tuesday 4:30pm to 5:40pm, oscar fencing"), only the first instance appeared in the calendar. Subsequent weeks showed no events.
- **Root Cause**: The frontend `wall.html` was calling the events API without the `expand=true` parameter, causing it to fetch only the master recurring event instead of expanded instances.
- **Fix**: Updated `frontend/wall.html` to add `&expand=true` to the events fetch URL (line 312)
- **Files Modified**: `frontend/wall.html`
- **Impact**: All recurring events now properly display all instances across the calendar view

#### Bug: Recurring Events Showing on Wrong Day of Week
- **Issue**: When creating "every Tuesday 4:30pm", events appeared on Monday instead of Tuesday
- **Root Cause**: RRULE weekday mismatch after timezone conversion
  - User: "every Tuesday 4:30pm Pacific"
  - Stored: Wednesday 12:30am UTC (correct conversion)
  - RRULE: `BYDAY=TU` (still says Tuesday)
  - Expansion: Finds next UTC Tuesday from Wednesday start → Wrong day
- **Fix**: Adjust RRULE weekday to match UTC weekday after timezone conversion
  - When converting local to UTC, check if weekday changed
  - If changed, adjust RRULE `BYDAY` to match the UTC weekday
  - Example: Tuesday 4:30pm PST → Wednesday 12:30am UTC → `BYDAY=TU` → `BYDAY=WE`
- **Files Modified**:
  - `app/services/nlp_service.py` - Calculate dates in user timezone (not server UTC)
  - `app/api/v1/endpoints/telegram.py` - Adjust RRULE on timezone conversion
  - `frontend/wall.html` - Added `expand=true` parameter
- **No Database Changes**: Simple logic fix, no migrations needed
- **Impact**: Recurring events now appear on the correct day of week

#### Documentation: Timezone Fix
- **Added**: Simple timezone fix guide at `docs/fixes/TIMEZONE.md`
- **Content**: Problem, root cause, solution, and testing steps
- **Added**: Rendering principles at `docs/RENDERING_PRINCIPLES.md`
- **Content**: Golden rule for UTC to local time conversion when displaying data

#### Future Enhancements
- WhatsApp integration (after business verification)
- Multi-timezone support per user
- Event editing via Telegram
- Event deletion via Telegram
- List events via Telegram
- Recurring event exceptions handling
- Voice message support
- Photo attachment support for event details
