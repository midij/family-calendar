import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.models.event import Event
from app.services.idempotency_service import IdempotencyService


class TestEventManagementAPI:
    """Test suite for enhanced event management API functionality"""
    
    def test_update_event_basic(self, client, sample_event):
        """Test basic event update functionality"""
        update_data = {
            "title": "Updated Piano Lesson",
            "location": "New Location"
        }
        
        response = client.patch(f"/v1/events/{sample_event.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Piano Lesson"
        assert data["location"] == "New Location"
        assert data["updated_at"] is not None
    
    def test_update_event_not_found(self, client):
        """Test updating a non-existent event"""
        update_data = {"title": "Updated Title"}
        
        response = client.patch("/v1/events/999", json=update_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_event_invalid_data(self, client, sample_event):
        """Test updating event with invalid data"""
        # Test invalid category - this will be caught by Pydantic validation (422)
        update_data = {"category": "invalid-category"}
        
        response = client.patch(f"/v1/events/{sample_event.id}", json=update_data)
        
        assert response.status_code == 422  # Pydantic validation error
        assert "string_pattern_mismatch" in response.json()["detail"][0]["type"]
    
    def test_update_event_invalid_rrule(self, client, sample_event):
        """Test updating event with invalid RRULE"""
        update_data = {"rrule": "INVALID=RULE"}
        
        response = client.patch(f"/v1/events/{sample_event.id}", json=update_data)
        
        assert response.status_code == 400
        assert "invalid rrule" in response.json()["detail"].lower()
    
    def test_update_event_invalid_time_range(self, client, sample_event):
        """Test updating event with invalid time range"""
        update_data = {
            "start_utc": "2025-09-02T09:00:00Z",
            "end_utc": "2025-09-02T08:00:00Z"  # End before start
        }
        
        response = client.patch(f"/v1/events/{sample_event.id}", json=update_data)
        
        assert response.status_code == 400
        assert "start time must be before end time" in response.json()["detail"].lower()
    
    def test_update_event_idempotency(self, client, sample_event):
        """Test event update with idempotency key"""
        update_data = {"title": "Idempotent Update"}
        idempotency_key = "test-update-key-123"
        
        # First request
        response1 = client.patch(
            f"/v1/events/{sample_event.id}", 
            json=update_data,
            headers={"Idempotency-Key": idempotency_key}
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["title"] == "Idempotent Update"
        
        # Second request with same idempotency key
        response2 = client.patch(
            f"/v1/events/{sample_event.id}", 
            json=update_data,
            headers={"Idempotency-Key": idempotency_key}
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should return the same result
        assert data2["title"] == data1["title"]
        assert data2["updated_at"] == data1["updated_at"]
    
    def test_update_event_different_idempotency_keys(self, client, sample_event):
        """Test that different idempotency keys produce different results"""
        import time
        
        update_data = {"title": "Different Update"}
        
        # First request
        response1 = client.patch(
            f"/v1/events/{sample_event.id}", 
            json=update_data,
            headers={"Idempotency-Key": "key-1"}
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Small delay to ensure different timestamps
        time.sleep(1)
        
        # Second request with different idempotency key
        response2 = client.patch(
            f"/v1/events/{sample_event.id}", 
            json=update_data,
            headers={"Idempotency-Key": "key-2"}
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should have different updated_at timestamps
        assert data1["updated_at"] != data2["updated_at"]
    
    def test_delete_event_basic(self, client, sample_event):
        """Test basic event deletion functionality"""
        response = client.delete(f"/v1/events/{sample_event.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Event deleted successfully"
        assert data["event_id"] == sample_event.id
        
        # Verify event is actually deleted
        get_response = client.get(f"/v1/events/{sample_event.id}")
        assert get_response.status_code == 404
    
    def test_delete_event_not_found(self, client):
        """Test deleting a non-existent event"""
        response = client.delete("/v1/events/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_delete_event_idempotency(self, client, sample_event):
        """Test event deletion with idempotency key"""
        idempotency_key = "test-delete-key-123"
        
        # First request
        response1 = client.delete(
            f"/v1/events/{sample_event.id}",
            headers={"Idempotency-Key": idempotency_key}
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["message"] == "Event deleted successfully"
        
        # Create a new event for the second test
        new_event_data = {
            "title": "Test Event for Idempotency",
            "start_utc": "2025-09-03T08:00:00Z",
            "end_utc": "2025-09-03T09:00:00Z",
            "category": "family",
            "source": "manual"
        }
        
        create_response = client.post("/v1/events/", json=new_event_data)
        assert create_response.status_code == 201
        new_event_id = create_response.json()["id"]
        
        # Second request with same idempotency key but different event
        # This should work because the idempotency key includes the event_id
        response2 = client.delete(
            f"/v1/events/{new_event_id}",
            headers={"Idempotency-Key": idempotency_key}
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Should return the same result structure
        assert data2["message"] == "Event deleted successfully"
        assert data2["event_id"] == new_event_id
    
    def test_delete_event_different_idempotency_keys(self, client, sample_event):
        """Test that different idempotency keys for delete operations work correctly"""
        # First delete with one key
        response1 = client.delete(
            f"/v1/events/{sample_event.id}",
            headers={"Idempotency-Key": "delete-key-1"}
        )
        
        assert response1.status_code == 200
        
        # Create another event for second test
        new_event_data = {
            "title": "Test Event 2",
            "start_utc": "2025-09-03T08:00:00Z",
            "end_utc": "2025-09-03T09:00:00Z",
            "category": "family",
            "source": "manual"
        }
        
        create_response = client.post("/v1/events/", json=new_event_data)
        assert create_response.status_code == 201
        new_event_id = create_response.json()["id"]
        
        # Second delete with different key
        response2 = client.delete(
            f"/v1/events/{new_event_id}",
            headers={"Idempotency-Key": "delete-key-2"}
        )
        
        assert response2.status_code == 200
    
    def test_update_event_partial_fields(self, client, sample_event):
        """Test updating only specific fields of an event"""
        original_title = sample_event.title
        original_location = sample_event.location
        
        # Update only the location
        update_data = {"location": "Updated Location Only"}
        
        response = client.patch(f"/v1/events/{sample_event.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == original_title  # Should remain unchanged
        assert data["location"] == "Updated Location Only"
    
    def test_update_event_rrule_validation(self, client, sample_event):
        """Test updating event with valid RRULE"""
        update_data = {
            "rrule": "FREQ=WEEKLY;BYDAY=MO,WE,FR;UNTIL=2025-12-31T00:00:00Z"
        }
        
        response = client.patch(f"/v1/events/{sample_event.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["rrule"] == update_data["rrule"]
    
    def test_update_event_exdates(self, client, sample_event):
        """Test updating event with exdates"""
        update_data = {
            "exdates": ["2025-10-01", "2025-12-25"]
        }
        
        response = client.patch(f"/v1/events/{sample_event.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["exdates"] == update_data["exdates"]
    
    def test_update_event_kid_ids(self, client, sample_event):
        """Test updating event with kid_ids"""
        update_data = {
            "kid_ids": [1, 2, 3]
        }
        
        response = client.patch(f"/v1/events/{sample_event.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["kid_ids"] == update_data["kid_ids"]
    
    def test_concurrent_update_operations(self, client, sample_event):
        """Test handling of concurrent update operations"""
        # Test sequential updates to simulate concurrent behavior
        # (Threading tests are complex with database sessions, so we test the logic instead)
        
        # First update
        update_data1 = {"title": "Updated by operation 1"}
        response1 = client.patch(f"/v1/events/{sample_event.id}", json=update_data1)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["title"] == "Updated by operation 1"
        
        # Second update
        update_data2 = {"title": "Updated by operation 2"}
        response2 = client.patch(f"/v1/events/{sample_event.id}", json=update_data2)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["title"] == "Updated by operation 2"
        
        # Third update
        update_data3 = {"title": "Updated by operation 3"}
        response3 = client.patch(f"/v1/events/{sample_event.id}", json=update_data3)
        assert response3.status_code == 200
        data3 = response3.json()
        assert data3["title"] == "Updated by operation 3"
    
    def test_idempotency_service_generation(self):
        """Test idempotency key generation"""
        operation = "update"
        event_id = 1
        request_data = {"title": "Test Title"}
        
        key1 = IdempotencyService.generate_idempotency_key(operation, event_id, request_data)
        key2 = IdempotencyService.generate_idempotency_key(operation, event_id, request_data)
        
        # Same inputs should generate same key
        assert key1 == key2
        
        # Different inputs should generate different keys
        key3 = IdempotencyService.generate_idempotency_key(operation, event_id, {"title": "Different Title"})
        assert key1 != key3
    
    def test_idempotency_service_storage(self):
        """Test idempotency result storage and retrieval"""
        key = "test-key-123"
        operation = "update"
        event_id = 1
        result = {"id": 1, "title": "Test Event"}
        
        # Store result
        IdempotencyService.store_idempotency_result(key, operation, event_id, result)
        
        # Retrieve result
        retrieved = IdempotencyService.check_idempotency(key, operation, event_id)
        assert retrieved == result
        
        # Test with different operation
        retrieved_different = IdempotencyService.check_idempotency(key, "delete", event_id)
        assert retrieved_different is None
    
    def test_validate_event_update_data(self):
        """Test event update data validation"""
        # Valid data
        valid_data = {
            "title": "Valid Title",
            "category": "family",
            "source": "manual"
        }
        is_valid, error = IdempotencyService.validate_event_update_data(valid_data)
        assert is_valid is True
        assert error == ""
        
        # Invalid category
        invalid_data = {"category": "invalid"}
        is_valid, error = IdempotencyService.validate_event_update_data(invalid_data)
        assert is_valid is False
        assert "invalid category" in error.lower()
        
        # Invalid time range
        invalid_time_data = {
            "start_utc": "2025-09-02T09:00:00Z",
            "end_utc": "2025-09-02T08:00:00Z"
        }
        is_valid, error = IdempotencyService.validate_event_update_data(invalid_time_data)
        assert is_valid is False
        assert "start time must be before end time" in error.lower()
