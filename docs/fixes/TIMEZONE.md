# Timezone Fix for Recurring Events

## The Problem
User says "every Tuesday 4:30pm" → Events show on Monday

## Why It Happened
```
User: "every Tuesday 4:30pm Pacific"
      ↓
Convert to UTC: Wednesday 12:30am UTC (correct)
RRULE says: BYDAY=TU (Tuesday) ← Wrong! Should be Wednesday in UTC
      ↓
Expansion: Finds UTC Tuesdays starting from Wednesday
      ↓  
Result: Shows on Monday Pacific ❌
```

## The Fix
When converting timezone shifts the day, adjust the RRULE to match.

**Where**: `app/api/v1/endpoints/telegram.py` in `confirm_event()`

**What**: After converting to UTC, if weekday changed, update RRULE:
- `BYDAY=TU` (local Tuesday) → `BYDAY=WE` (UTC Wednesday)

## Principle
- **Store everything in UTC** ✓
- **Display in user's local time** ✓ (browser handles this)
- **RRULE weekday must match UTC weekday** ✓ (the fix)

## Testing
```bash
docker-compose restart web

# Via Telegram:
"every Tuesday 4:30pm to 5:40pm, oscar fencing"

# Should now show on Tuesday ✅
```

## Files Changed
1. `app/services/nlp_service.py` - Calculate dates in user timezone
2. `app/api/v1/endpoints/telegram.py` - Adjust RRULE on conversion
3. `frontend/wall.html` - Added `expand=true` parameter
