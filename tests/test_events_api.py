import pytest
from datetime import datetime, timezone
from app.models.event import Event


class TestEventsAPI:
    """Test suite for Events API endpoints"""
    
    def test_get_events_empty(self, client):
        """Test getting events when database is empty"""
        response = client.get("/v1/events/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_events_with_data(self, client, sample_event):
        """Test getting events when data exists"""
        response = client.get("/v1/events/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "钢琴课"
        assert data[0]["location"] == "艺术中心302"
        assert data[0]["category"] == "after-school"
        assert data[0]["kid_ids"] == ["1"]
        assert "id" in data[0]
        assert "created_at" in data[0]
    
    def test_get_event_by_id(self, client, sample_event):
        """Test getting a specific event by ID"""
        response = client.get(f"/v1/events/{sample_event.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "钢琴课"
        assert data["id"] == sample_event.id
    
    def test_get_event_not_found(self, client):
        """Test getting an event that doesn't exist"""
        response = client.get("/v1/events/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_create_event(self, client, sample_event_data):
        """Test creating a new event"""
        response = client.post("/v1/events/", json=sample_event_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == sample_event_data["title"]
        assert data["location"] == sample_event_data["location"]
        assert data["category"] == sample_event_data["category"]
        assert data["kid_ids"] == sample_event_data["kid_ids"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_event_missing_required_fields(self, client):
        """Test creating an event with missing required fields"""
        incomplete_data = {"title": "Test Event"}
        response = client.post("/v1/events/", json=incomplete_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_event_invalid_category(self, client):
        """Test creating an event with invalid category"""
        invalid_data = {
            "title": "Test Event",
            "start_utc": "2025-09-02T08:00:00Z",
            "end_utc": "2025-09-02T09:00:00Z",
            "category": "invalid-category",
            "source": "manual"
        }
        response = client.post("/v1/events/", json=invalid_data)
        assert response.status_code == 422
    
    def test_create_event_invalid_source(self, client):
        """Test creating an event with invalid source"""
        invalid_data = {
            "title": "Test Event",
            "start_utc": "2025-09-02T08:00:00Z",
            "end_utc": "2025-09-02T09:00:00Z",
            "category": "family",
            "source": "invalid-source"
        }
        response = client.post("/v1/events/", json=invalid_data)
        assert response.status_code == 422
    
    def test_update_event(self, client, sample_event):
        """Test updating an event"""
        update_data = {
            "title": "Updated Title",
            "location": "Updated Location"
        }
        response = client.patch(f"/v1/events/{sample_event.id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["location"] == "Updated Location"
        assert data["id"] == sample_event.id
        assert "updated_at" in data
    
    def test_update_event_not_found(self, client):
        """Test updating an event that doesn't exist"""
        update_data = {"title": "Updated Title"}
        response = client.patch("/v1/events/999", json=update_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_delete_event(self, client, sample_event):
        """Test deleting an event"""
        response = client.delete(f"/v1/events/{sample_event.id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify event is deleted
        get_response = client.get(f"/v1/events/{sample_event.id}")
        assert get_response.status_code == 404
    
    def test_delete_event_not_found(self, client):
        """Test deleting an event that doesn't exist"""
        response = client.delete("/v1/events/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_filter_events_by_category(self, client, db_session):
        """Test filtering events by category"""
        # Create events with different categories
        event1 = Event(
            title="School Event",
            start_utc=datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
            category="school",
            source="manual"
        )
        event2 = Event(
            title="Family Event",
            start_utc=datetime(2025, 9, 2, 10, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 2, 11, 0, 0, tzinfo=timezone.utc),
            category="family",
            source="manual"
        )
        
        db_session.add_all([event1, event2])
        db_session.commit()
        
        # Test filtering by school category
        response = client.get("/v1/events/?category=school")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "school"
        
        # Test filtering by family category
        response = client.get("/v1/events/?category=family")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "family"
    
    def test_filter_events_by_kid_id(self, client, db_session):
        """Test filtering events by kid_id"""
        # Create events with different kid_ids
        event1 = Event(
            title="Event for Kid 1",
            start_utc=datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
            kid_ids=["1"],
            category="family",
            source="manual"
        )
        event2 = Event(
            title="Event for Kid 2",
            start_utc=datetime(2025, 9, 2, 10, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 2, 11, 0, 0, tzinfo=timezone.utc),
            kid_ids=["2"],
            category="family",
            source="manual"
        )
        
        db_session.add_all([event1, event2])
        db_session.commit()
        
        # Test filtering by kid_id
        response = client.get("/v1/events/?kid_id=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["kid_ids"] == ["1"]
    
    def test_filter_events_by_date_range(self, client, db_session):
        """Test filtering events by date range"""
        # Create events on different dates
        event1 = Event(
            title="Early Event",
            start_utc=datetime(2025, 9, 1, 8, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 1, 9, 0, 0, tzinfo=timezone.utc),
            category="family",
            source="manual"
        )
        event2 = Event(
            title="Late Event",
            start_utc=datetime(2025, 9, 3, 8, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 3, 9, 0, 0, tzinfo=timezone.utc),
            category="family",
            source="manual"
        )
        
        db_session.add_all([event1, event2])
        db_session.commit()
        
        # Test filtering by start date
        response = client.get("/v1/events/?start=2025-09-02T00:00:00Z")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Late Event"
        
        # Test filtering by end date
        response = client.get("/v1/events/?end=2025-09-02T00:00:00Z")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Early Event"
    
    def test_events_ordering(self, client, db_session):
        """Test that events are returned ordered by start time"""
        # Create events with different start times
        event1 = Event(
            title="Late Event",
            start_utc=datetime(2025, 9, 2, 10, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 2, 11, 0, 0, tzinfo=timezone.utc),
            category="family",
            source="manual"
        )
        event2 = Event(
            title="Early Event",
            start_utc=datetime(2025, 9, 2, 8, 0, 0, tzinfo=timezone.utc),
            end_utc=datetime(2025, 9, 2, 9, 0, 0, tzinfo=timezone.utc),
            category="family",
            source="manual"
        )
        
        db_session.add_all([event1, event2])
        db_session.commit()
        
        response = client.get("/v1/events/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Early Event"  # Should come first
        assert data[1]["title"] == "Late Event"   # Should come second
    
    def test_event_with_json_fields(self, client):
        """Test creating and retrieving events with JSON fields (kid_ids, exdates)"""
        event_data = {
            "title": "Test Event with JSON",
            "start_utc": "2025-09-02T08:00:00Z",
            "end_utc": "2025-09-02T09:00:00Z",
            "kid_ids": ["1", "2", "3"],
            "exdates": ["2025-10-01", "2025-11-01"],
            "category": "family",
            "source": "manual"
        }
        
        # Create event
        response = client.post("/v1/events/", json=event_data)
        assert response.status_code == 200
        
        created_event = response.json()
        assert created_event["kid_ids"] == ["1", "2", "3"]
        assert created_event["exdates"] == ["2025-10-01", "2025-11-01"]
        
        # Retrieve event
        event_id = created_event["id"]
        response = client.get(f"/v1/events/{event_id}")
        assert response.status_code == 200
        
        retrieved_event = response.json()
        assert retrieved_event["kid_ids"] == ["1", "2", "3"]
        assert retrieved_event["exdates"] == ["2025-10-01", "2025-11-01"]
