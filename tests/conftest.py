import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.models.kid import Kid
from app.models.event import Event
from app.main import app
from datetime import datetime, timezone

# Create a temporary SQLite database for testing
@pytest.fixture(scope="session")
def test_db():
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield TestingSessionLocal
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def db_session(test_db):
    """Create a fresh database session for each test"""
    session = test_db()
    try:
        # Clear all data before each test
        session.query(Event).delete()
        session.query(Kid).delete()
        session.commit()
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db_session):
    """Create a test client with database dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def sample_kid_data():
    """Sample kid data for testing"""
    return {
        "name": "小明",
        "color": "#4f46e5",
        "avatar": "https://example.com/avatar1.jpg"
    }

@pytest.fixture
def sample_event_data():
    """Sample event data for testing"""
    return {
        "title": "钢琴课",
        "location": "艺术中心302",
        "start_utc": datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
        "end_utc": datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
        "rrule": "FREQ=WEEKLY;BYDAY=TU,TH;UNTIL=2025-12-20T00:00:00Z",
        "exdates": ["2025-10-01"],
        "kid_ids": [1],
        "category": "after-school",
        "source": "manual",
        "created_by": "admin"
    }

@pytest.fixture
def sample_kid(db_session, sample_kid_data):
    """Create a sample kid in the database"""
    kid = Kid(**sample_kid_data)
    db_session.add(kid)
    db_session.commit()
    db_session.refresh(kid)
    return kid

@pytest.fixture
def sample_event_api_data():
    """Sample event data for API testing (with ISO strings)"""
    return {
        "title": "钢琴课",
        "location": "艺术中心302",
        "start_utc": "2025-09-02T08:00:00Z",
        "end_utc": "2025-09-02T09:00:00Z",
        "rrule": "FREQ=WEEKLY;BYDAY=TU,TH;UNTIL=2025-12-20T00:00:00Z",
        "exdates": ["2025-10-01"],
        "kid_ids": [1],
        "category": "after-school",
        "source": "manual",
        "created_by": "admin"
    }

@pytest.fixture
def sample_event(db_session, sample_event_data):
    """Create a sample event in the database"""
    event = Event(**sample_event_data)
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event
