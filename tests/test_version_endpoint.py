"""
Tests for the version endpoint that provides database timestamp-based polling
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.event import Event
from app.models.kid import Kid
from app.database import get_db

class TestVersionEndpoint:
    """Test the GET /v1/events/version endpoint"""
    
    def test_version_endpoint_no_events(self, client, db_session):
        """Test version endpoint when no events exist"""
        response = client.get("/v1/events/version")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "last_updated" in data
        assert "timestamp" in data
        assert data["last_updated"] is None
        assert data["timestamp"] is not None
        
        # Verify timestamp is recent (within last minute)
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        assert (now - timestamp).total_seconds() < 60
    
    def test_version_endpoint_with_events(self, client, db_session):
        """Test version endpoint with existing events"""
        # Create a test event
        event = Event(
            title="Test Event",
            start_utc=datetime.now(timezone.utc),
            end_utc=datetime.now(timezone.utc) + timedelta(hours=1),
            category="family",
            source="manual"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        
        response = client.get("/v1/events/version")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "last_updated" in data
        assert "timestamp" in data
        assert data["last_updated"] is not None
        
        # Verify last_updated matches the event's updated_at
        last_updated = datetime.fromisoformat(data["last_updated"].replace("Z", "+00:00"))
        assert abs((last_updated - event.updated_at).total_seconds()) < 1
    
    def test_version_endpoint_multiple_events(self, client, db_session):
        """Test version endpoint returns latest updated_at from multiple events"""
        # Create events with different timestamps
        now = datetime.now(timezone.utc)
        
        event1 = Event(
            title="Event 1",
            start_utc=now,
            end_utc=now + timedelta(hours=1),
            category="family",
            source="manual"
        )
        db_session.add(event1)
        db_session.commit()
        db_session.refresh(event1)
        
        # Wait a moment to ensure different timestamps (SQLite rounds to seconds)
        import time
        time.sleep(1.1)
        
        event2 = Event(
            title="Event 2",
            start_utc=now + timedelta(hours=2),
            end_utc=now + timedelta(hours=3),
            category="family",
            source="manual"
        )
        db_session.add(event2)
        db_session.commit()
        db_session.refresh(event2)
        
        response = client.get("/v1/events/version")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return the latest updated_at (event2)
        last_updated = datetime.fromisoformat(data["last_updated"].replace("Z", "+00:00"))
        assert abs((last_updated - event2.updated_at).total_seconds()) < 1
        assert event2.updated_at > event1.updated_at
    
    def test_version_endpoint_updates_after_event_creation(self, client, db_session):
        """Test that version endpoint updates after creating new events"""
        # Get initial version
        response1 = client.get("/v1/events/version")
        initial_data = response1.json()
        
        # Create a new event
        event_data = {
            "title": "New Event",
            "start_utc": datetime.now(timezone.utc).isoformat(),
            "end_utc": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "category": "family",
            "source": "manual"
        }
        
        create_response = client.post("/v1/events/", json=event_data)
        assert create_response.status_code == 201
        
        # Get version after creation
        response2 = client.get("/v1/events/version")
        updated_data = response2.json()
        
        # Version should have changed
        assert updated_data["last_updated"] != initial_data["last_updated"]
        assert updated_data["last_updated"] is not None
    
    def test_version_endpoint_updates_after_event_update(self, client, db_session):
        """Test that version endpoint updates after modifying events"""
        # Create an event
        event = Event(
            title="Original Title",
            start_utc=datetime.now(timezone.utc),
            end_utc=datetime.now(timezone.utc) + timedelta(hours=1),
            category="family",
            source="manual"
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        
        # Get initial version
        response1 = client.get("/v1/events/version")
        initial_data = response1.json()
        
        # Wait a moment to ensure timestamp difference (SQLite rounds to seconds)
        import time
        time.sleep(1.1)
        
        # Update the event
        update_data = {"title": "Updated Title"}
        update_response = client.patch(f"/v1/events/{event.id}", json=update_data)
        assert update_response.status_code == 200
        
        # Get version after update
        response2 = client.get("/v1/events/version")
        updated_data = response2.json()
        
        # Version should have changed
        assert updated_data["last_updated"] != initial_data["last_updated"]
        
        # Parse timestamps and verify the new one is later
        initial_time = datetime.fromisoformat(initial_data["last_updated"].replace("Z", "+00:00"))
        updated_time = datetime.fromisoformat(updated_data["last_updated"].replace("Z", "+00:00"))
        assert updated_time > initial_time
    
    def test_version_endpoint_updates_after_event_deletion(self, client, db_session):
        """Test that version endpoint updates after deleting events"""
        # Create two events with different timestamps
        now = datetime.now(timezone.utc)
        
        event1 = Event(
            title="Event 1",
            start_utc=now,
            end_utc=now + timedelta(hours=1),
            category="family",
            source="manual"
        )
        db_session.add(event1)
        db_session.commit()
        db_session.refresh(event1)
        
        # Wait to ensure different timestamps
        import time
        time.sleep(1.1)
        
        event2 = Event(
            title="Event 2",
            start_utc=now + timedelta(hours=2),
            end_utc=now + timedelta(hours=3),
            category="family",
            source="manual"
        )
        db_session.add(event2)
        db_session.commit()
        db_session.refresh(event2)
        
        # Get version with both events
        response1 = client.get("/v1/events/version")
        initial_data = response1.json()
        
        # Delete the newer event
        delete_response = client.delete(f"/v1/events/{event2.id}")
        assert delete_response.status_code == 200
        
        # Get version after deletion
        response2 = client.get("/v1/events/version")
        updated_data = response2.json()
        
        # Version should have changed (now reflects event1's timestamp)
        assert updated_data["last_updated"] != initial_data["last_updated"]
        
        # Should now reflect event1's updated_at
        last_updated = datetime.fromisoformat(updated_data["last_updated"].replace("Z", "+00:00"))
        assert abs((last_updated - event1.updated_at).total_seconds()) < 1
    
    def test_version_endpoint_performance(self, client, db_session):
        """Test that version endpoint performs well with many events"""
        # Create many events
        now = datetime.now(timezone.utc)
        events = []
        
        for i in range(100):
            event = Event(
                title=f"Event {i}",
                start_utc=now + timedelta(hours=i),
                end_utc=now + timedelta(hours=i+1),
                category="family",
                source="manual"
            )
            events.append(event)
        
        db_session.add_all(events)
        db_session.commit()
        
        # Test version endpoint performance
        import time
        start_time = time.time()
        
        response = client.get("/v1/events/version")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 0.1  # Should respond in under 100ms
        
        data = response.json()
        assert data["last_updated"] is not None
