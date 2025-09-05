#!/usr/bin/env python3
"""
Manual test script for the version endpoint
Run this after starting the server with: uvicorn app.main:app --reload
"""
import requests
import json
from datetime import datetime, timezone

def test_version_endpoint():
    """Test the version endpoint manually"""
    base_url = "http://localhost:8000"
    
    print("Testing Family Calendar Version Endpoint")
    print("=" * 50)
    
    try:
        # Test version endpoint
        print("1. Testing GET /v1/events/version")
        response = requests.get(f"{base_url}/v1/events/version")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            
            # Verify response structure
            assert "last_updated" in data, "Missing 'last_updated' field"
            assert "timestamp" in data, "Missing 'timestamp' field"
            
            print("   ✅ Version endpoint working correctly!")
            
            # Test creating an event and checking version change
            print("\n2. Testing version change after event creation")
            
            # Get initial version
            initial_response = requests.get(f"{base_url}/v1/events/version")
            initial_data = initial_response.json()
            print(f"   Initial version: {initial_data['last_updated']}")
            
            # Create a test event
            event_data = {
                "title": "Test Event for Version Check",
                "start_utc": datetime.now(timezone.utc).isoformat(),
                "end_utc": (datetime.now(timezone.utc).replace(hour=23, minute=59)).isoformat(),
                "category": "family",
                "source": "manual"
            }
            
            create_response = requests.post(f"{base_url}/v1/events/", json=event_data)
            print(f"   Create event status: {create_response.status_code}")
            
            if create_response.status_code == 201:
                # Check version after creation
                updated_response = requests.get(f"{base_url}/v1/events/version")
                updated_data = updated_response.json()
                print(f"   Updated version: {updated_data['last_updated']}")
                
                if updated_data['last_updated'] != initial_data['last_updated']:
                    print("   ✅ Version changed after event creation!")
                else:
                    print("   ⚠️  Version didn't change (might be same timestamp)")
                
                # Clean up - delete the test event
                event_id = create_response.json()['id']
                delete_response = requests.delete(f"{base_url}/v1/events/{event_id}")
                print(f"   Cleanup delete status: {delete_response.status_code}")
                
        else:
            print(f"   ❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the server is running:")
        print("   uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_version_endpoint()
