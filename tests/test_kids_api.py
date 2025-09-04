import pytest
from fastapi.testclient import TestClient
from app.models.kid import Kid


class TestKidsAPI:
    """Test suite for Kids API endpoints"""
    
    def test_get_kids_empty(self, client):
        """Test getting kids when database is empty"""
        response = client.get("/v1/kids/")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_kids_with_data(self, client, sample_kid):
        """Test getting kids when data exists"""
        response = client.get("/v1/kids/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "小明"
        assert data[0]["color"] == "#4f46e5"
        assert data[0]["avatar"] == "https://example.com/avatar1.jpg"
        assert "id" in data[0]
        assert "created_at" in data[0]
    
    def test_get_kid_by_id(self, client, sample_kid):
        """Test getting a specific kid by ID"""
        response = client.get(f"/v1/kids/{sample_kid.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "小明"
        assert data["id"] == sample_kid.id
    
    def test_get_kid_not_found(self, client):
        """Test getting a kid that doesn't exist"""
        response = client.get("/v1/kids/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_create_kid(self, client, sample_kid_data):
        """Test creating a new kid"""
        response = client.post("/v1/kids/", json=sample_kid_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == sample_kid_data["name"]
        assert data["color"] == sample_kid_data["color"]
        assert data["avatar"] == sample_kid_data["avatar"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_kid_missing_required_fields(self, client):
        """Test creating a kid with missing required fields"""
        incomplete_data = {"name": "Test Kid"}
        response = client.post("/v1/kids/", json=incomplete_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_kid_invalid_data(self, client):
        """Test creating a kid with invalid data"""
        invalid_data = {
            "name": "",  # Empty name
            "color": "invalid-color",  # Invalid color format
            "avatar": "not-a-url"
        }
        response = client.post("/v1/kids/", json=invalid_data)
        assert response.status_code == 422
    
    def test_delete_kid(self, client, sample_kid):
        """Test deleting a kid"""
        response = client.delete(f"/v1/kids/{sample_kid.id}")
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify kid is deleted
        get_response = client.get(f"/v1/kids/{sample_kid.id}")
        assert get_response.status_code == 404
    
    def test_delete_kid_not_found(self, client):
        """Test deleting a kid that doesn't exist"""
        response = client.delete("/v1/kids/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_kids_ordering(self, client, db_session):
        """Test that kids are returned in alphabetical order by name"""
        # Create multiple kids with different names
        kid1 = Kid(name="Charlie", color="#ff0000")
        kid2 = Kid(name="Alice", color="#00ff00")
        kid3 = Kid(name="Bob", color="#0000ff")
        
        db_session.add_all([kid1, kid2, kid3])
        db_session.commit()
        
        response = client.get("/v1/kids/")
        assert response.status_code == 200
        
        data = response.json()
        names = [kid["name"] for kid in data]
        assert names == sorted(names)  # Should be in alphabetical order
