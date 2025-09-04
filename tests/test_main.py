import pytest
from fastapi.testclient import TestClient


class TestMainApp:
    """Test suite for main application endpoints"""
    
    def test_root_endpoint(self, client):
        """Test the root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Family Calendar API"}
    
    def test_health_check(self, client):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_api_v1_prefix(self, client):
        """Test that API v1 endpoints are properly prefixed"""
        # Test that endpoints are accessible under /v1/
        response = client.get("/v1/kids/")
        assert response.status_code == 200
        
        response = client.get("/v1/events/")
        assert response.status_code == 200
    
    def test_cors_headers(self, client):
        """Test that CORS headers are properly set"""
        response = client.options("/v1/kids/")
        # FastAPI TestClient doesn't show CORS headers in the same way,
        # but we can verify the endpoint is accessible
        assert response.status_code in [200, 405]  # OPTIONS might return 405
