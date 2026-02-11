# Rendering Principles

## Golden Rule: Always Convert UTC to Local Time for Display

### Storage Layer (Database)
- ✅ **Always store in UTC**: `start_utc`, `end_utc`
- ✅ **RRULE weekday in UTC**: `BYDAY=WE` matches UTC weekday

### Display Layer (Frontend)
- ✅ **Always convert to local time**: User sees their timezone
- ✅ **RRULE weekday in local**: Show `BYDAY=TU` (local Tuesday)

## Implementation

### JavaScript Date Conversion
```javascript
// API returns UTC timestamp
const utcTime = "2026-02-12T00:30:00Z";

// Convert to local time (automatic)
const localDate = new Date(utcTime);
// localDate is now in browser's timezone

// Display as local time
localDate.toLocaleString();  // "2/11/2026, 4:30:00 PM" (Pacific)
localDate.toLocaleDateString();  // "2/11/2026"
localDate.toLocaleTimeString();  // "4:30:00 PM"
```

### RRULE Conversion
```javascript
// Stored RRULE (UTC weekday)
const storedRRule = "FREQ=WEEKLY;BYDAY=WE";  // Wednesday UTC

// Convert for display (local weekday)
const localStartDate = new Date(event.start_utc);  // Auto converts to local
const localWeekday = localStartDate.getDay();  // 2 (Tuesday)
const dayMap = ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'];
const displayRRule = `FREQ=WEEKLY;BYDAY=${dayMap[localWeekday]}`;
// Result: "FREQ=WEEKLY;BYDAY=TU" (Tuesday local)
```

## Checklist for Every Rendering

When displaying any datetime from the API:

1. ✅ Is it in UTC? (yes, all API times are UTC)
2. ✅ Convert to `new Date()` (automatic timezone conversion)
3. ✅ Use `.toLocaleString()` or similar for display
4. ✅ For RRULE: Convert weekday to match local time

## Common Mistakes

❌ **Don't display UTC directly**
```javascript
// Wrong
<div>{event.start_utc}</div>  // Shows "2026-02-12T00:30:00Z"
```

✅ **Always convert first**
```javascript
// Correct
const localDate = new Date(event.start_utc);
<div>{localDate.toLocaleString()}</div>  // Shows "2/11/2026, 4:30:00 PM"
```

❌ **Don't show UTC weekday in RRULE**
```javascript
// Wrong
<div>RRULE: {event.rrule}</div>  // Shows "BYDAY=WE" (UTC Wednesday)
```

✅ **Convert to local weekday**
```javascript
// Correct
const localRRule = convertRRuleToLocalTime(event.rrule, new Date(event.start_utc));
<div>RRULE: {localRRule} (Local Time)</div>  // Shows "BYDAY=TU" (Tuesday local)
```

## Files Using This Principle

1. `frontend/wall.html` - Calendar display
2. `frontend/admin.html` - Admin panel list and edit form

## Testing

Always test with different timezones:
- Test in Pacific Time (PST/PDT)
- Test with events that cross day boundaries (e.g., 11:30pm local = next day UTC)
- Verify RRULE weekday matches the displayed day
