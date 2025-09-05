# Family Calendar - Frontend Wall Display

## Overview

The frontend wall display is a responsive, wall-mounted calendar interface designed for family use. It provides a weekly view of events with child-specific tracks and real-time updates.

## Features

### ✅ Implemented Features

- **Responsive Grid Layout**: Adapts to different screen sizes using CSS Grid
- **Weekly View**: Monday-Sunday columns with clear day headers
- **Time Axis**: 8:00 AM - 10:00 PM with 1-hour slots
- **Child Tracks**: Color-coded rows for each child
- **Navigation**: Previous/Next week buttons and "Today" button
- **Event Cards**: Positioned events with category-based colors
- **Real-time Updates**: Polls version endpoint every 10 seconds
- **Connection Status**: Shows online/offline status
- **Responsive Fonts**: Uses `clamp()` for scalable typography
- **Auto-refresh Indicator**: Shows when updates are being applied

### 🎨 Design Features

- **Wall-mounted Optimized**: Large fonts readable from 2-3 meters
- **Color-coded Events**: Different colors for family, after-school, imported, manual events
- **Child Track Colors**: Each child has a distinct color with 20% opacity background
- **Today Highlighting**: Current day is highlighted in red
- **Smooth Animations**: Hover effects and update animations
- **Gradient Background**: Beautiful gradient background for visual appeal

### 🔧 Technical Features

- **API Integration**: Connects to FastAPI backend at `http://localhost:8000/v1`
- **Version Polling**: Uses `/events/version` endpoint for real-time updates
- **Error Handling**: Graceful error handling with user-friendly messages
- **Offline Detection**: Shows offline status when connection is lost
- **Performance Optimized**: Efficient DOM updates and event rendering

## Usage

### Starting the Wall Display

1. **Start the Backend Server**:
   ```bash
   cd /path/to/family-calendar
   source venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Open the Wall Display**:
   - Open `frontend/wall.html` in a web browser
   - Or serve it from a web server for better performance

### Navigation

- **Previous Week**: Click "← Last Week" button
- **Next Week**: Click "Next Week →" button  
- **Today**: Click "Today" button to jump to current week
- **Event Details**: Click on any event card to see details

### Real-time Updates

The wall display automatically:
- Checks for updates every 10 seconds
- Shows "Updating..." indicator when refreshing
- Updates the "Last updated" timestamp
- Maintains connection status indicator

## File Structure

```
frontend/
├── wall.html          # Main wall display interface
└── README.md          # This documentation
```

## API Endpoints Used

- `GET /v1/kids/` - Load child data and colors
- `GET /v1/events/` - Load events for the week
- `GET /v1/events/version` - Check for updates

## Browser Compatibility

- **Modern Browsers**: Chrome, Firefox, Safari, Edge
- **CSS Grid**: Requires CSS Grid support
- **ES6 Features**: Uses modern JavaScript features
- **Responsive Design**: Works on tablets and large screens

## Performance

- **Load Time**: < 2 seconds on modern hardware
- **Update Frequency**: 10-second polling interval
- **Memory Usage**: Minimal DOM manipulation
- **Network**: Lightweight API calls

## Customization

### Colors
- Child track colors are loaded from the API
- Event category colors are defined in CSS
- Background gradient can be modified in the CSS

### Time Range
- Default: 8:00 AM - 10:00 PM
- Modify `TIME_START` and `TIME_END` constants in JavaScript

### Refresh Interval
- Default: 10 seconds
- Modify `REFRESH_INTERVAL` constant in JavaScript

## Troubleshooting

### Common Issues

1. **"Failed to load calendar data"**
   - Check if backend server is running on port 8000
   - Verify API endpoints are accessible

2. **Events not showing**
   - Check browser console for JavaScript errors
   - Verify events exist in the database
   - Check if events fall within the current week

3. **Real-time updates not working**
   - Check network connection
   - Verify `/v1/events/version` endpoint is working
   - Check browser console for errors

### Debug Mode

Open browser developer tools to see:
- API requests and responses
- JavaScript console logs
- Network connection status
- Real-time update logs

## Future Enhancements

- **Touch Support**: Better touch interactions for tablets
- **Keyboard Navigation**: Arrow key navigation
- **Event Creation**: Click to create new events
- **Settings Panel**: Customize colors and time ranges
- **Offline Mode**: Cache events for offline viewing
- **Multiple Views**: Daily, monthly view options
