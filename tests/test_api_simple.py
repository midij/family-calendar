import pytest
import requests
import time
import subprocess
import signal
import os
from threading import Thread


class TestAPISimple:
    """Simple API tests using requests (requires server to be running)"""
    
    @pytest.fixture(scope="class")
    def server_process(self):
        """Start the server for testing"""
        # Start the server in a subprocess
        process = subprocess.Popen(
            ["python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        time.sleep(3)
        
        yield process
        
        # Cleanup
        process.terminate()
        process.wait()
    
    def test_server_health(self, server_process):
        """Test that the server is running and healthy"""
        response = requests.get("http://127.0.0.1:8001/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_root_endpoint(self, server_process):
        """Test the root endpoint"""
        response = requests.get("http://127.0.0.1:8001/")
        assert response.status_code == 200
        assert response.json() == {"message": "Family Calendar API"}
    
    def test_kids_endpoint(self, server_process):
        """Test the kids endpoint"""
        response = requests.get("http://127.0.0.1:8001/v1/kids/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_events_endpoint(self, server_process):
        """Test the events endpoint"""
        response = requests.get("http://127.0.0.1:8001/v1/events/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_kid(self, server_process):
        """Test creating a kid"""
        kid_data = {
            "name": "Test Kid",
            "color": "#ff0000",
            "avatar": "https://example.com/test.jpg"
        }
        
        response = requests.post("http://127.0.0.1:8001/v1/kids/", json=kid_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == kid_data["name"]
        assert data["color"] == kid_data["color"]
        assert data["avatar"] == kid_data["avatar"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_event(self, server_process):
        """Test creating an event"""
        event_data = {
            "title": "Test Event",
            "start_utc": "2025-09-05T10:00:00Z",
            "end_utc": "2025-09-05T11:00:00Z",
            "kid_ids": ["1"],
            "category": "family",
            "source": "manual"
        }
        
        response = requests.post("http://127.0.0.1:8001/v1/events/", json=event_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == event_data["title"]
        assert data["kid_ids"] == event_data["kid_ids"]
        assert data["category"] == event_data["category"]
        assert "id" in data
        assert "created_at" in data
    
    def test_invalid_event_creation(self, server_process):
        """Test creating an event with invalid data"""
        invalid_data = {
            "title": "Test Event",
            "start_utc": "2025-09-05T10:00:00Z",
            "end_utc": "2025-09-05T11:00:00Z",
            "category": "invalid-category",  # Invalid category
            "source": "manual"
        }
        
        response = requests.post("http://127.0.0.1:8001/v1/events/", json=invalid_data)
        assert response.status_code == 422  # Validation error
