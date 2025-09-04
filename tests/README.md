# Family Calendar API Tests

This directory contains comprehensive tests for the Family Calendar API.

## Test Structure

- `conftest.py` - Test configuration, fixtures, and database setup
- `test_main.py` - Tests for main application endpoints
- `test_kids_api.py` - Tests for Kids API endpoints
- `test_events_api.py` - Tests for Events API endpoints

## Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Run with verbose output
python run_tests.py --verbose

# Run with coverage report
python run_tests.py --coverage

# Run specific test file
python run_tests.py --file test_kids_api.py
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_kids_api.py

# Run specific test class
pytest tests/test_kids_api.py::TestKidsAPI

# Run specific test method
pytest tests/test_kids_api.py::TestKidsAPI::test_get_kids_empty

# Run with coverage
pytest --cov=app --cov-report=html
```

## Test Features

### Database Testing
- Uses temporary SQLite database for each test session
- Fresh database session for each test
- Automatic cleanup after tests

### API Testing
- Full HTTP client testing with FastAPI TestClient
- Tests all CRUD operations
- Tests query parameters and filtering
- Tests error handling and validation

### Test Coverage
- **Kids API**: GET, POST, DELETE operations
- **Events API**: GET, POST, PATCH, DELETE operations
- **Query Parameters**: Date range, kid_id, category filtering
- **Error Handling**: 404, 422 validation errors
- **Data Validation**: Required fields, data types, constraints

## Test Data

Tests use fixtures for consistent test data:
- `sample_kid_data` - Sample kid data for testing
- `sample_event_data` - Sample event data for testing
- `sample_kid` - Creates a kid in the database
- `sample_event` - Creates an event in the database

## Adding New Tests

1. Create test files following the pattern `test_*.py`
2. Use the existing fixtures for consistent test data
3. Follow the naming convention: `test_<functionality>`
4. Add appropriate assertions for both success and error cases
5. Use markers for test categorization:
   - `@pytest.mark.unit` - Unit tests
   - `@pytest.mark.integration` - Integration tests
   - `@pytest.mark.slow` - Slow tests

## Example Test

```python
def test_create_kid(self, client, sample_kid_data):
    """Test creating a new kid"""
    response = client.post("/v1/kids/", json=sample_kid_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == sample_kid_data["name"]
    assert "id" in data
    assert "created_at" in data
```

## Continuous Integration

The test suite is designed to run in CI/CD environments:
- No external dependencies (uses temporary database)
- Fast execution
- Comprehensive coverage
- Clear error reporting
