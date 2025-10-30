"""
Test suite for the Parent Admin Interface
Tests the admin.html functionality and user workflows
"""

import pytest
import requests
import json
import time
from datetime import datetime, timedelta


class AdminInterfaceTester:
    """Test suite for Admin Interface functionality"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_url = f"{self.base_url}/v1"
        self.session = requests.Session()
        self.test_kid_id = None
        self.test_event_id = None
    
    def test_admin_html_accessibility(self):
        """Test that admin.html is accessible and contains required elements"""
        print("\n🧪 Testing Admin HTML Accessibility...")
        
        response = self.session.get(f"{self.base_url}/frontend/admin.html")
        assert response.status_code == 200, f"Admin HTML not accessible: {response.status_code}"
        
        content = response.text
        
        # Check for essential features
        required_features = [
            "kidForm", "eventForm", "Bulk Operations", "Import CSV", 
            "Import ICS", "Export Data", "wall.html", "API_BASE_URL"
        ]
        
        for feature in required_features:
            assert feature in content, f"Missing feature: {feature}"
        
        print("✅ Admin HTML accessibility test passed")
    
    def test_kids_management_workflow(self):
        """Test complete kids management workflow"""
        print("\n🧪 Testing Kids Management Workflow...")
        
        # Test creating a kid
        kid_data = {
            "name": "Test Admin Kid",
            "color": "#ff6b6b",
            "avatar": "https://example.com/test-admin.jpg"
        }
        
        response = self.session.post(f"{self.api_url}/kids/", json=kid_data)
        assert response.status_code == 201, f"Failed to create kid: {response.status_code}"
        
        created_kid = response.json()
        self.test_kid_id = created_kid["id"]
        
        assert created_kid["name"] == kid_data["name"]
        assert created_kid["color"] == kid_data["color"]
        assert created_kid["avatar"] == kid_data["avatar"]
        
        print(f"✅ Created kid: {created_kid['name']} (ID: {created_kid['id']})")
        
        # Test updating the kid
        update_data = {
            "name": "Updated Admin Kid",
            "color": "#4ecdc4",
            "avatar": "https://example.com/updated-admin.jpg"
        }
        
        response = self.session.patch(f"{self.api_url}/kids/{self.test_kid_id}", json=update_data)
        assert response.status_code == 200, f"Failed to update kid: {response.status_code}"
        
        updated_kid = response.json()
        assert updated_kid["name"] == update_data["name"]
        assert updated_kid["color"] == update_data["color"]
        
        print(f"✅ Updated kid: {updated_kid['name']}")
        
        # Test getting the kid
        response = self.session.get(f"{self.api_url}/kids/{self.test_kid_id}")
        assert response.status_code == 200, f"Failed to get kid: {response.status_code}"
        
        retrieved_kid = response.json()
        assert retrieved_kid["name"] == update_data["name"]
        
        print("✅ Kids management workflow test passed")
    
    def test_events_management_workflow(self):
        """Test complete events management workflow"""
        print("\n🧪 Testing Events Management Workflow...")
        
        # Test creating an event
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        event_data = {
            "title": "Test Admin Event",
            "location": "Test Location",
            "start_utc": start_time.isoformat() + "Z",
            "end_utc": end_time.isoformat() + "Z",
            "kid_ids": [self.test_kid_id] if self.test_kid_id else None,
            "category": "family",
            "source": "manual"
        }
        
        response = self.session.post(f"{self.api_url}/events/", json=event_data)
        assert response.status_code == 201, f"Failed to create event: {response.status_code}"
        
        created_event = response.json()
        self.test_event_id = created_event["id"]
        
        assert created_event["title"] == event_data["title"]
        assert created_event["location"] == event_data["location"]
        assert created_event["category"] == event_data["category"]
        
        print(f"✅ Created event: {created_event['title']} (ID: {created_event['id']})")
        
        # Test updating the event
        update_data = {
            "title": "Updated Admin Event",
            "location": "Updated Location",
            "category": "education"
        }
        
        response = self.session.patch(f"{self.api_url}/events/{self.test_event_id}", json=update_data)
        assert response.status_code == 200, f"Failed to update event: {response.status_code}"
        
        updated_event = response.json()
        assert updated_event["title"] == update_data["title"]
        assert updated_event["location"] == update_data["location"]
        assert updated_event["category"] == update_data["category"]
        
        print(f"✅ Updated event: {updated_event['title']}")
        
        # Test getting the event
        response = self.session.get(f"{self.api_url}/events/{self.test_event_id}")
        assert response.status_code == 200, f"Failed to get event: {response.status_code}"
        
        retrieved_event = response.json()
        assert retrieved_event["title"] == update_data["title"]
        
        print("✅ Events management workflow test passed")
    
    def test_bulk_operations(self):
        """Test bulk operations (import/export)"""
        print("\n🧪 Testing Bulk Operations...")
        
        # Test CSV template download (simulated)
        csv_template = """title,location,start_date,start_time,end_date,end_time,kid_ids,category,rrule
"Test Event","Test Location","2025-09-15","10:00","2025-09-15","11:00","1","family","" """
        
        # Test export functionality (get current data)
        response = self.session.get(f"{self.api_url}/kids/")
        assert response.status_code == 200, "Failed to get kids for export"
        
        response = self.session.get(f"{self.api_url}/events/")
        assert response.status_code == 200, "Failed to get events for export"
        
        print("✅ Bulk operations test passed")
    
    def test_form_validation(self):
        """Test form validation and error handling"""
        print("\n🧪 Testing Form Validation...")
        
        # Test invalid kid data
        invalid_kid_data = {
            "name": "",  # Empty name should fail
            "color": "invalid-color",  # Invalid color format
            "avatar": "not-a-url"  # Invalid URL
        }
        
        response = self.session.post(f"{self.api_url}/kids/", json=invalid_kid_data)
        assert response.status_code in [400, 422], f"Should reject invalid kid data: {response.status_code}"
        
        # Test invalid event data
        invalid_event_data = {
            "title": "",  # Empty title should fail
            "start_utc": "invalid-date",  # Invalid date format
            "end_utc": "invalid-date",
            "category": "invalid-category",  # Invalid category
            "source": "manual"
        }
        
        response = self.session.post(f"{self.api_url}/events/", json=invalid_event_data)
        assert response.status_code in [400, 422], f"Should reject invalid event data: {response.status_code}"
        
        print("✅ Form validation test passed")
    
    def test_responsive_design(self):
        """Test responsive design elements"""
        print("\n🧪 Testing Responsive Design...")
        
        response = self.session.get(f"{self.base_url}/frontend/admin.html")
        content = response.text
        
        # Check for responsive design elements
        responsive_elements = [
            "@media", "grid-template-columns", "flex", "clamp("
        ]
        
        for element in responsive_elements:
            assert element in content, f"Missing responsive element: {element}"
        
        print("✅ Responsive design test passed")
    
    def test_navigation_integration(self):
        """Test navigation between admin and wall display"""
        print("\n🧪 Testing Navigation Integration...")
        
        # Test wall display accessibility
        response = self.session.get(f"{self.base_url}/frontend/wall.html")
        assert response.status_code == 200, "Wall display not accessible"
        
        # Check for admin link in wall display
        content = response.text
        assert "admin.html" in content, "Admin link missing from wall display"
        
        # Test admin display accessibility
        response = self.session.get(f"{self.base_url}/frontend/admin.html")
        assert response.status_code == 200, "Admin display not accessible"
        
        # Check for wall display link in admin
        content = response.text
        assert "wall.html" in content, "Wall display link missing from admin"
        
        print("✅ Navigation integration test passed")
    
    def test_user_experience_features(self):
        """Test user experience features"""
        print("\n🧪 Testing User Experience Features...")
        
        response = self.session.get(f"{self.base_url}/frontend/admin.html")
        content = response.text
        
        # Check for UX features
        ux_features = [
            "loading", "status-message", "hover", "transition", 
            "backdrop-filter", "box-shadow", "border-radius"
        ]
        
        for feature in ux_features:
            assert feature in content, f"Missing UX feature: {feature}"
        
        print("✅ User experience features test passed")
    
    def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        if self.test_event_id:
            try:
                response = self.session.delete(f"{self.api_url}/events/{self.test_event_id}")
                if response.status_code == 200:
                    print(f"✅ Cleaned up test event {self.test_event_id}")
            except Exception as e:
                print(f"⚠️ Failed to clean up test event: {e}")
        
        if self.test_kid_id:
            try:
                response = self.session.delete(f"{self.api_url}/kids/{self.test_kid_id}")
                if response.status_code == 200:
                    print(f"✅ Cleaned up test kid {self.test_kid_id}")
            except Exception as e:
                print(f"⚠️ Failed to clean up test kid: {e}")
    
    def run_all_tests(self):
        """Run all admin interface tests"""
        print("🧪 Starting Admin Interface Tests")
        print("=" * 50)
        
        try:
            self.test_admin_html_accessibility()
            self.test_kids_management_workflow()
            self.test_events_management_workflow()
            self.test_bulk_operations()
            self.test_form_validation()
            self.test_responsive_design()
            self.test_navigation_integration()
            self.test_user_experience_features()
            
            print("\n" + "=" * 50)
            print("🎉 All Admin Interface Tests PASSED!")
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            return False
        finally:
            self.cleanup()


def test_admin_interface():
    """Main test function for admin interface"""
    tester = AdminInterfaceTester()
    result = tester.run_all_tests()
    assert result is True, "Admin interface tests failed"


if __name__ == "__main__":
    test_admin_interface()
