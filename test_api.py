#!/usr/bin/env python3
"""
Simple API test script for Family Calendar
Run this after making changes to test all API endpoints
"""

import requests
import json
import time
from datetime import datetime, timezone


class APITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health(self):
        """Test server health"""
        print("🔍 Testing server health...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ Server is healthy")
                return True
            else:
                print(f"❌ Server health check failed: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
            return False
    
    def test_kids_api(self):
        """Test Kids API endpoints"""
        print("\n👶 Testing Kids API...")
        
        # Test GET /v1/kids/
        response = self.session.get(f"{self.base_url}/v1/kids/")
        if response.status_code == 200:
            print("✅ GET /v1/kids/ - OK")
            kids = response.json()
            print(f"   Found {len(kids)} kids")
        else:
            print(f"❌ GET /v1/kids/ - Failed: {response.status_code}")
            return False
        
        # Test POST /v1/kids/
        kid_data = {
            "name": "Test Kid",
            "color": "#ff0000",
            "avatar": "https://example.com/test.jpg"
        }
        response = self.session.post(f"{self.base_url}/v1/kids/", json=kid_data)
        if response.status_code == 200:
            print("✅ POST /v1/kids/ - OK")
            created_kid = response.json()
            kid_id = created_kid["id"]
        else:
            print(f"❌ POST /v1/kids/ - Failed: {response.status_code}")
            return False
        
        # Test GET /v1/kids/{id}
        response = self.session.get(f"{self.base_url}/v1/kids/{kid_id}")
        if response.status_code == 200:
            print("✅ GET /v1/kids/{id} - OK")
        else:
            print(f"❌ GET /v1/kids/{id} - Failed: {response.status_code}")
            return False
        
        # Test DELETE /v1/kids/{id}
        response = self.session.delete(f"{self.base_url}/v1/kids/{kid_id}")
        if response.status_code == 200:
            print("✅ DELETE /v1/kids/{id} - OK")
        else:
            print(f"❌ DELETE /v1/kids/{id} - Failed: {response.status_code}")
            return False
        
        return True
    
    def test_events_api(self):
        """Test Events API endpoints"""
        print("\n📅 Testing Events API...")
        
        # Test GET /v1/events/
        response = self.session.get(f"{self.base_url}/v1/events/")
        if response.status_code == 200:
            print("✅ GET /v1/events/ - OK")
            events = response.json()
            print(f"   Found {len(events)} events")
        else:
            print(f"❌ GET /v1/events/ - Failed: {response.status_code}")
            return False
        
        # Test POST /v1/events/
        event_data = {
            "title": "Test Event",
            "location": "Test Location",
            "start_utc": "2025-09-05T10:00:00Z",
            "end_utc": "2025-09-05T11:00:00Z",
            "kid_ids": ["1"],
            "category": "family",
            "source": "manual"
        }
        response = self.session.post(f"{self.base_url}/v1/events/", json=event_data)
        if response.status_code == 200:
            print("✅ POST /v1/events/ - OK")
            created_event = response.json()
            event_id = created_event["id"]
        else:
            print(f"❌ POST /v1/events/ - Failed: {response.status_code}")
            return False
        
        # Test GET /v1/events/{id}
        response = self.session.get(f"{self.base_url}/v1/events/{event_id}")
        if response.status_code == 200:
            print("✅ GET /v1/events/{id} - OK")
        else:
            print(f"❌ GET /v1/events/{id} - Failed: {response.status_code}")
            return False
        
        # Test PATCH /v1/events/{id}
        update_data = {"title": "Updated Test Event"}
        response = self.session.patch(f"{self.base_url}/v1/events/{event_id}", json=update_data)
        if response.status_code == 200:
            print("✅ PATCH /v1/events/{id} - OK")
        else:
            print(f"❌ PATCH /v1/events/{id} - Failed: {response.status_code}")
            return False
        
        # Test query parameters
        response = self.session.get(f"{self.base_url}/v1/events/?category=family")
        if response.status_code == 200:
            print("✅ GET /v1/events/?category=family - OK")
        else:
            print(f"❌ GET /v1/events/?category=family - Failed: {response.status_code}")
            return False
        
        # Test DELETE /v1/events/{id}
        response = self.session.delete(f"{self.base_url}/v1/events/{event_id}")
        if response.status_code == 200:
            print("✅ DELETE /v1/events/{id} - OK")
        else:
            print(f"❌ DELETE /v1/events/{id} - Failed: {response.status_code}")
            return False
        
        return True
    
    def test_error_handling(self):
        """Test error handling"""
        print("\n🚨 Testing Error Handling...")
        
        # Test 404 for non-existent kid
        response = self.session.get(f"{self.base_url}/v1/kids/999")
        if response.status_code == 404:
            print("✅ GET /v1/kids/999 (404) - OK")
        else:
            print(f"❌ GET /v1/kids/999 (404) - Failed: {response.status_code}")
            return False
        
        # Test 404 for non-existent event
        response = self.session.get(f"{self.base_url}/v1/events/999")
        if response.status_code == 404:
            print("✅ GET /v1/events/999 (404) - OK")
        else:
            print(f"❌ GET /v1/events/999 (404) - Failed: {response.status_code}")
            return False
        
        # Test validation error
        invalid_data = {
            "title": "Test Event",
            "start_utc": "2025-09-05T10:00:00Z",
            "end_utc": "2025-09-05T11:00:00Z",
            "category": "invalid-category",
            "source": "manual"
        }
        response = self.session.post(f"{self.base_url}/v1/events/", json=invalid_data)
        if response.status_code == 422:
            print("✅ POST /v1/events/ with invalid data (422) - OK")
        else:
            print(f"❌ POST /v1/events/ with invalid data (422) - Failed: {response.status_code}")
            return False
        
        return True
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting API Tests for Family Calendar")
        print("=" * 50)
        
        if not self.test_health():
            return False
        
        if not self.test_kids_api():
            return False
        
        if not self.test_events_api():
            return False
        
        if not self.test_error_handling():
            return False
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Your API is working correctly.")
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Family Calendar API")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for the API")
    parser.add_argument("--wait", type=int, default=0, help="Wait N seconds before starting tests")
    
    args = parser.parse_args()
    
    if args.wait > 0:
        print(f"⏳ Waiting {args.wait} seconds before starting tests...")
        time.sleep(args.wait)
    
    tester = APITester(args.url)
    success = tester.run_all_tests()
    
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
