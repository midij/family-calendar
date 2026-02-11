# Testing Guide for Family Calendar API

This guide explains how to test the Family Calendar API after making changes.

## Quick Start

### 1. Start the Server
```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Run API Tests
```bash
# In another terminal, run the comprehensive API test
python test_api.py

# Or with a delay if server is starting
python test_api.py --wait 3
```

## Testing Options

### Option 1: Simple API Test (Recommended)
The `test_api.py` script provides comprehensive testing of all API endpoints:

```bash
# Test with default settings (localhost:8088)
python test_api.py

# Test with custom URL
python test_api.py --url http://localhost:8001

# Wait before testing (useful if server is starting)
python test_api.py --wait 5
```

**What it tests:**
- ✅ Server health check
- ✅ Kids API (GET, POST, DELETE)
- ✅ Events API (GET, POST, PATCH, DELETE)
- ✅ Query parameters and filtering
- ✅ Error handling (404, 422)
- ✅ Data validation

### Option 2: Unit Tests with pytest
For more detailed testing of individual components:

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_models.py

# Run with coverage report
python -m pytest --cov=app --cov-report=html
```

**Available test files:**
- `tests/test_models.py` - Database model tests
- `tests/test_kids_api.py` - Kids API tests (requires TestClient fix)
- `tests/test_events_api.py` - Events API tests (requires TestClient fix)
- `tests/test_main.py` - Main application tests

### Option 3: Manual Testing with curl
For quick manual testing:

```bash
# Test health
curl http://localhost:8088/health

# Get all kids
curl http://localhost:8088/v1/kids/

# Create a kid
curl -X POST http://localhost:8088/v1/kids/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Kid", "color": "#ff0000"}'

# Get all events
curl http://localhost:8088/v1/events/

# Create an event
curl -X POST http://localhost:8088/v1/events/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Event",
    "start_utc": "2025-09-05T10:00:00Z",
    "end_utc": "2025-09-05T11:00:00Z",
    "category": "family",
    "source": "manual"
  }'
```

## Test Coverage

### API Endpoints Tested
| Method | Endpoint | Status |
|--------|----------|---------|
| GET | `/health` | ✅ |
| GET | `/` | ✅ |
| GET | `/v1/kids/` | ✅ |
| GET | `/v1/kids/{id}` | ✅ |
| POST | `/v1/kids/` | ✅ |
| DELETE | `/v1/kids/{id}` | ✅ |
| GET | `/v1/events/` | ✅ |
| GET | `/v1/events/{id}` | ✅ |
| POST | `/v1/events/` | ✅ |
| PATCH | `/v1/events/{id}` | ✅ |
| DELETE | `/v1/events/{id}` | ✅ |

### Query Parameters Tested
- ✅ Date range filtering (`start`, `end`)
- ✅ Kid filtering (`kid_id`)
- ✅ Category filtering (`category`)

### Error Handling Tested
- ✅ 404 errors for non-existent resources
- ✅ 422 validation errors for invalid data
- ✅ Required field validation
- ✅ Data type validation

### Data Validation Tested
- ✅ JSON field handling (kid_ids, exdates)
- ✅ Category validation (school, after-school, family)
- ✅ Source validation (manual, ics, google, outlook)
- ✅ Date format validation

## After Making Changes

### 1. Test Your Changes
```bash
# Start server
uvicorn app.main:app --reload

# Run comprehensive tests
python test_api.py
```

### 2. If Tests Fail
1. Check the error messages
2. Verify your changes don't break existing functionality
3. Test the specific endpoint manually with curl
4. Check server logs for detailed error information

### 3. Add New Tests
If you add new functionality, add tests to `test_api.py`:

```python
def test_new_feature(self):
    """Test new feature"""
    response = self.session.get(f"{self.base_url}/v1/new-endpoint/")
    assert response.status_code == 200
    print("✅ New feature works!")
```

## Troubleshooting

### Server Won't Start
```bash
# Check if port is in use
lsof -i :8088

# Kill existing process
pkill -f uvicorn

# Start fresh
uvicorn app.main:app --reload
```

### Tests Fail with Connection Error
- Make sure server is running on the correct port
- Check if server is accessible: `curl http://localhost:8088/health`
- Try different port: `python test_api.py --url http://localhost:8001`

### Database Issues
- Check if database file exists: `ls -la family_calendar.db`
- Reset database: `rm family_calendar.db && alembic upgrade head`

## Continuous Integration

For automated testing in CI/CD:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python test_api.py --url http://localhost:8088
```

## Performance Testing

For basic performance testing:

```bash
# Test with multiple requests
for i in {1..10}; do
  curl -s http://localhost:8088/v1/events/ > /dev/null
  echo "Request $i completed"
done
```

## Summary

The testing setup provides:
- ✅ **Simple API testing** with `test_api.py`
- ✅ **Unit testing** with pytest
- ✅ **Manual testing** with curl
- ✅ **Comprehensive coverage** of all endpoints
- ✅ **Error handling** validation
- ✅ **Data validation** testing

Use `python test_api.py` after making any changes to ensure everything still works correctly!
