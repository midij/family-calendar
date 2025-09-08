# Family Calendar

A wall-mounted calendar system designed for multi-child families to coordinate school activities, after-school programs, family events, and transportation arrangements.

## Features

- Weekly calendar view (Monday-Sunday)
- Child-specific event tracking with color coding
- Recurring event support (RRULE)
- Real-time updates via Server-Sent Events
- CSV and ICS file import capabilities
- Responsive design for wall mounting

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+

### Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd family-calendar
```

2. Start the services:
```bash
docker-compose up -d
```

3. Run database migrations:
```bash
docker exec -it family-calendar-app-1 alembic upgrade head
```

4. Access the API:
- API: http://localhost:8000
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs

### Local Development

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /v1/kids` - Get all kids
- `POST /v1/kids` - Create a new kid
- `GET /v1/events` - Get events with filtering
- `POST /v1/events` - Create a new event

## Project Structure

```
app/
├── __init__.py
├── main.py
├── config.py
├── database.py
├── models/
│   ├── __init__.py
│   ├── base.py
│   ├── kid.py
│   └── event.py
├── schemas/
│   ├── __init__.py
│   ├── kid.py
│   └── event.py
└── api/
    └── v1/
        ├── __init__.py
        ├── api.py
        └── endpoints/
            ├── __init__.py
            ├── kids.py
            └── events.py
```

## Testing

Run the test suite:
```bash
pytest
```

## License

MIT

```

## 7. Create a simple test script

```python:test_setup.py
#!/usr/bin/env python3
"""
Simple test script to verify the basic setup is working
"""

import requests
import time
import sys

def test_api_health():
    """Test if the API is responding"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ API health check passed")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API - is it running?")
        return False

def test_database_connection():
    """Test if the database is accessible"""
    try:
        response = requests.get("http://localhost:8000/v1/kids")
        if response.status_code == 200:
            print("✅ Database connection working")
            return True
        else:
            print(f"❌ Database connection failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API")
        return False

def main():
    print("🧪 Testing Family Calendar Setup...")
    print("=" * 40)
    
    # Wait a bit for services to start
    print("⏳ Waiting for services to start...")
    time.sleep(5)
    
    # Test API health
    api_ok = test_api_health()
    
    # Test database connection
    db_ok = test_database_connection()
    
    print("=" * 40)
    if api_ok and db_ok:
        print("🎉 All tests passed! Setup is working correctly.")
        return 0
    else:
        print(" Some tests failed. Please check the setup.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

Now let's test the setup:

## Test Plan Execution

1. **Start the services:**
```bash
docker-compose up -d
```

2. **Run database migrations:**
```bash
docker exec -it family-calendar-app-1 alembic upgrade head
```

3. **Test the setup:**
```bash
python test_setup.py
```

## Summary of Task 1 Implementation

✅ **Project Structure Created**: Complete directory structure with proper Python packages
✅ **Docker Setup**: Dockerfile and docker-compose.yml with SQLite database
✅ **Python Environment**: requirements.txt with all necessary dependencies
✅ **Database Models**: SQLAlchemy models for Kid and Event with proper relationships
✅ **API Structure**: FastAPI application with basic endpoints for kids and events
✅ **Configuration**: Environment-based configuration with Pydantic settings
✅ **Database Migrations**: Alembic setup for database schema management
✅ **Basic Testing**: Simple test script to verify setup

The project is now ready for development with:
- FastAPI backend with proper API structure
- SQLite database with real-time polling
- Docker containerization for easy development
- Database migration system
- Basic CRUD endpoints for kids and events

**Task 1 Status: ✅ DONE**

You can now proceed to Task 2 (Database Schema & Models) or test the current setup first. Would you like me to help you test the setup or move on to the next task? 