#!/usr/bin/env python3
"""
Comprehensive End-to-End Test Suite for Family Calendar
Tests complete user workflows, performance, and system integration
"""

import pytest
import requests
import time
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
import statistics


class E2ETestSuite:
    """Comprehensive end-to-end test suite for Family Calendar"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.performance_metrics = {}
        self.test_data = {}
    
    def setup_test_data(self):
        """Setup test data for comprehensive testing"""
        print("🔧 Setting up test data...")
        
        # Create test kids
        kids_data = [
            {"name": "E2E Test Kid 1", "color": "#ff6b6b", "avatar": "https://example.com/kid1.jpg"},
            {"name": "E2E Test Kid 2", "color": "#4ecdc4", "avatar": "https://example.com/kid2.jpg"},
            {"name": "E2E Test Kid 3", "color": "#45b7d1", "avatar": "https://example.com/kid3.jpg"}
        ]
        
        self.test_data["kids"] = []
        for kid_data in kids_data:
            response = self.session.post(f"{self.base_url}/v1/kids/", json=kid_data)
            assert response.status_code == 201
            self.test_data["kids"].append(response.json())
        
        # Create test events
        events_data = [
            {
                "title": "E2E Test Event 1",
                "location": "Test Location 1",
                "start_utc": "2025-09-05T10:00:00Z",
                "end_utc": "2025-09-05T11:00:00Z",
                "kid_ids": [str(self.test_data["kids"][0]["id"])],
                "category": "family",
                "source": "manual"
            },
            {
                "title": "E2E Test Recurring Event",
                "location": "Test Location 2",
                "start_utc": "2025-09-06T14:00:00Z",
                "end_utc": "2025-09-06T15:00:00Z",
                "rrule": "FREQ=WEEKLY;BYDAY=FR;UNTIL=2025-12-20T00:00:00Z",
                "kid_ids": [str(self.test_data["kids"][1]["id"])],
                "category": "after-school",
                "source": "manual"
            },
            {
                "title": "E2E Test Multi-Kid Event",
                "location": "Test Location 3",
                "start_utc": "2025-09-07T16:00:00Z",
                "end_utc": "2025-09-07T17:00:00Z",
                "kid_ids": [str(self.test_data["kids"][0]["id"]), str(self.test_data["kids"][2]["id"])],
                "category": "family",
                "source": "manual"
            }
        ]
        
        self.test_data["events"] = []
        for event_data in events_data:
            response = self.session.post(f"{self.base_url}/v1/events/", json=event_data)
            assert response.status_code == 201
            self.test_data["events"].append(response.json())
        
        print(f"✅ Created {len(self.test_data['kids'])} test kids and {len(self.test_data['events'])} test events")
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("🧹 Cleaning up test data...")
        
        # Delete test events
        for event in self.test_data.get("events", []):
            response = self.session.delete(f"{self.base_url}/v1/events/{event['id']}")
            assert response.status_code == 200
        
        # Delete test kids
        for kid in self.test_data.get("kids", []):
            response = self.session.delete(f"{self.base_url}/v1/kids/{kid['id']}")
            assert response.status_code == 200
        
        print("✅ Test data cleaned up")
    
    def measure_performance(self, operation_name: str, operation_func, *args, **kwargs):
        """Measure performance of an operation"""
        start_time = time.time()
        result = operation_func(*args, **kwargs)
        end_time = time.time()
        
        duration = (end_time - start_time) * 1000  # Convert to milliseconds
        self.performance_metrics[operation_name] = duration
        
        print(f"⏱️  {operation_name}: {duration:.2f}ms")
        return result, duration
    
    def test_complete_user_workflow(self):
        """Test complete user workflow: create kid → create event → view calendar → update event → delete event"""
        print("\n🔄 Testing Complete User Workflow...")
        
        # Step 1: Create a new kid
        kid_data = {
            "name": "Workflow Test Kid",
            "color": "#ff9ff3",
            "avatar": "https://example.com/workflow.jpg"
        }
        response, duration = self.measure_performance(
            "Create Kid",
            lambda: self.session.post(f"{self.base_url}/v1/kids/", json=kid_data)
        )
        assert response.status_code == 201
        assert duration <= 300  # API should respond within 300ms
        created_kid = response.json()
        
        # Step 2: Create an event for the kid
        event_data = {
            "title": "Workflow Test Event",
            "location": "Workflow Location",
            "start_utc": "2025-09-08T10:00:00Z",
            "end_utc": "2025-09-08T11:00:00Z",
            "kid_ids": [str(created_kid["id"])],
            "category": "family",
            "source": "manual"
        }
        response, duration = self.measure_performance(
            "Create Event",
            lambda: self.session.post(f"{self.base_url}/v1/events/", json=event_data)
        )
        assert response.status_code == 201
        assert duration <= 300
        created_event = response.json()
        
        # Step 3: View calendar (get events for the week)
        week_start = "2025-09-08T00:00:00Z"
        week_end = "2025-09-14T23:59:59Z"
        response, duration = self.measure_performance(
            "Get Weekly Events",
            lambda: self.session.get(f"{self.base_url}/v1/events/?start={week_start}&end={week_end}")
        )
        assert response.status_code == 200
        assert duration <= 300
        events = response.json()
        assert len(events) >= 1  # Should include our created event
        
        # Step 4: Update the event
        update_data = {"title": "Updated Workflow Test Event"}
        response, duration = self.measure_performance(
            "Update Event",
            lambda: self.session.patch(f"{self.base_url}/v1/events/{created_event['id']}", json=update_data)
        )
        assert response.status_code == 200
        assert duration <= 300
        
        # Step 5: Verify the update
        response, duration = self.measure_performance(
            "Get Updated Event",
            lambda: self.session.get(f"{self.base_url}/v1/events/{created_event['id']}")
        )
        assert response.status_code == 200
        assert duration <= 300
        updated_event = response.json()
        assert updated_event["title"] == "Updated Workflow Test Event"
        
        # Step 6: Delete the event
        response, duration = self.measure_performance(
            "Delete Event",
            lambda: self.session.delete(f"{self.base_url}/v1/events/{created_event['id']}")
        )
        assert response.status_code == 200
        assert duration <= 300
        
        # Step 7: Delete the kid
        response, duration = self.measure_performance(
            "Delete Kid",
            lambda: self.session.delete(f"{self.base_url}/v1/kids/{created_kid['id']}")
        )
        assert response.status_code == 200
        assert duration <= 300
        
        print("✅ Complete user workflow test passed")
    
    def test_performance_requirements(self):
        """Test performance requirements: ≤300ms API, ≤1s render"""
        print("\n⚡ Testing Performance Requirements...")
        
        # Test API response times
        api_tests = [
            ("Health Check", lambda: self.session.get(f"{self.base_url}/health")),
            ("Get Kids", lambda: self.session.get(f"{self.base_url}/v1/kids/")),
            ("Get Events", lambda: self.session.get(f"{self.base_url}/v1/events/")),
            ("Get Events with Date Range", lambda: self.session.get(f"{self.base_url}/v1/events/?start=2025-09-01T00:00:00Z&end=2025-09-30T23:59:59Z")),
            ("Get Weekly Events", lambda: self.session.get(f"{self.base_url}/v1/events/weekly/?week_start=2025-09-01T00:00:00Z")),
            ("Get Daily Events", lambda: self.session.get(f"{self.base_url}/v1/events/daily/?day=2025-09-05T00:00:00Z")),
            ("Get Expanded Events", lambda: self.session.get(f"{self.base_url}/v1/events/expanded/")),
            ("Get Version", lambda: self.session.get(f"{self.base_url}/v1/events/version"))
        ]
        
        api_times = []
        for test_name, test_func in api_tests:
            response, duration = self.measure_performance(test_name, test_func)
            assert response.status_code == 200
            assert duration <= 300, f"{test_name} took {duration:.2f}ms, exceeds 300ms limit"
            api_times.append(duration)
        
        # Calculate statistics
        avg_api_time = statistics.mean(api_times)
        max_api_time = max(api_times)
        min_api_time = min(api_times)
        
        print(f"📊 API Performance Statistics:")
        print(f"   Average: {avg_api_time:.2f}ms")
        print(f"   Maximum: {max_api_time:.2f}ms")
        print(f"   Minimum: {min_api_time:.2f}ms")
        
        # Test frontend render time (simulate by measuring API calls needed for full page load)
        start_time = time.time()
        
        # Simulate frontend loading sequence
        self.session.get(f"{self.base_url}/v1/kids/")
        self.session.get(f"{self.base_url}/v1/events/?start=2025-09-01T00:00:00Z&end=2025-09-07T23:59:59Z")
        self.session.get(f"{self.base_url}/v1/events/version")
        
        end_time = time.time()
        render_time = (end_time - start_time) * 1000
        
        print(f"🎨 Simulated Frontend Render Time: {render_time:.2f}ms")
        assert render_time <= 1000, f"Frontend render time {render_time:.2f}ms exceeds 1s limit"
        
        print("✅ Performance requirements test passed")
    
    def test_rrule_complexity(self):
        """Test complex RRULE scenarios and event expansion"""
        print("\n🔄 Testing RRULE Complexity...")
        
        # Test complex recurring event
        complex_rrule_data = {
            "title": "Complex RRULE Test",
            "location": "Complex Location",
            "start_utc": "2025-09-09T09:00:00Z",
            "end_utc": "2025-09-09T10:00:00Z",
            "rrule": "FREQ=WEEKLY;BYDAY=MO,WE,FR;UNTIL=2025-12-20T00:00:00Z",
            "exdates": ["2025-10-13", "2025-11-27"],  # Skip some instances
            "kid_ids": [str(self.test_data["kids"][0]["id"])],
            "category": "after-school",
            "source": "manual"
        }
        
        response, duration = self.measure_performance(
            "Create Complex RRULE Event",
            lambda: self.session.post(f"{self.base_url}/v1/events/", json=complex_rrule_data)
        )
        assert response.status_code == 201
        assert duration <= 300
        complex_event = response.json()
        
        # Test event expansion
        response, duration = self.measure_performance(
            "Expand Complex RRULE Event",
            lambda: self.session.get(f"{self.base_url}/v1/events/{complex_event['id']}/expand")
        )
        assert response.status_code == 200
        assert duration <= 300
        expanded_instances = response.json()
        assert len(expanded_instances) > 10  # Should have many instances
        
        # Test RRULE validation
        rrule_tests = [
            ("Valid Weekly", "FREQ=WEEKLY;BYDAY=TU,TH", True),
            ("Valid Monthly", "FREQ=MONTHLY;BYMONTHDAY=15", True),
            ("Valid Yearly", "FREQ=YEARLY;BYMONTH=6;BYMONTHDAY=15", True),
            ("Empty Rule (One-time event)", "", True),  # Empty RRULE is valid for one-time events
            ("Invalid Rule", "INVALID=RULE", False)
        ]
        
        for test_name, rrule_str, expected_valid in rrule_tests:
            response, duration = self.measure_performance(
                f"Validate RRULE: {test_name}",
                lambda: self.session.post(f"{self.base_url}/v1/events/validate-rrule?rrule_str={rrule_str}")
            )
            assert response.status_code == 200
            assert duration <= 300
            validation_result = response.json()
            
            assert validation_result["valid"] is expected_valid, f"RRULE validation for {test_name} expected {expected_valid}, got {validation_result['valid']}"
        
        # Clean up
        self.session.delete(f"{self.base_url}/v1/events/{complex_event['id']}")
        
        print("✅ RRULE complexity test passed")
    
    def test_concurrent_operations(self):
        """Test concurrent operations and race conditions"""
        print("\n🔄 Testing Concurrent Operations...")
        
        import threading
        import queue
        
        results = queue.Queue()
        errors = queue.Queue()
        
        def concurrent_operation(operation_id):
            try:
                # Each thread creates a kid and an event
                kid_data = {
                    "name": f"Concurrent Kid {operation_id}",
                    "color": f"#{operation_id:06x}",
                    "avatar": f"https://example.com/concurrent{operation_id}.jpg"
                }
                
                kid_response = self.session.post(f"{self.base_url}/v1/kids/", json=kid_data)
                if kid_response.status_code != 201:
                    errors.put(f"Thread {operation_id}: Failed to create kid")
                    return
                
                kid = kid_response.json()
                
                event_data = {
                    "title": f"Concurrent Event {operation_id}",
                    "location": f"Concurrent Location {operation_id}",
                    "start_utc": f"2025-09-{10 + operation_id}T10:00:00Z",
                    "end_utc": f"2025-09-{10 + operation_id}T11:00:00Z",
                    "kid_ids": [str(kid["id"])],
                    "category": "family",
                    "source": "manual"
                }
                
                event_response = self.session.post(f"{self.base_url}/v1/events/", json=event_data)
                if event_response.status_code != 201:
                    errors.put(f"Thread {operation_id}: Failed to create event")
                    return
                
                event = event_response.json()
                
                # Clean up
                self.session.delete(f"{self.base_url}/v1/events/{event['id']}")
                self.session.delete(f"{self.base_url}/v1/kids/{kid['id']}")
                
                results.put(f"Thread {operation_id}: Success")
                
            except Exception as e:
                errors.put(f"Thread {operation_id}: Exception - {str(e)}")
        
        # Run 5 concurrent operations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=concurrent_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = results.qsize()
        error_count = errors.qsize()
        
        print(f"📊 Concurrent Operations Results:")
        print(f"   Successful: {success_count}")
        print(f"   Errors: {error_count}")
        
        # Print any errors
        while not errors.empty():
            print(f"   ❌ {errors.get()}")
        
        assert error_count == 0, f"Concurrent operations failed: {error_count} errors"
        assert success_count == 5, f"Expected 5 successful operations, got {success_count}"
        
        print("✅ Concurrent operations test passed")
    
    def test_error_handling_and_edge_cases(self):
        """Test error handling and edge cases"""
        print("\n🚨 Testing Error Handling and Edge Cases...")
        
        # Test invalid data
        invalid_tests = [
            ("Invalid Kid Data", "/v1/kids/", {"name": "", "color": "invalid-color"}),
            ("Invalid Event Data", "/v1/events/", {"title": "", "start_utc": "invalid-date"}),
            ("Missing Required Fields", "/v1/events/", {"title": "Test"}),  # Missing required fields
            ("Invalid Date Range", "/v1/events/", {
                "title": "Test",
                "start_utc": "2025-09-05T11:00:00Z",
                "end_utc": "2025-09-05T10:00:00Z",  # End before start
                "category": "family",
                "source": "manual"
            })
        ]
        
        for test_name, endpoint, data in invalid_tests:
            response = self.session.post(f"{self.base_url}{endpoint}", json=data)
            assert response.status_code in [400, 422], f"{test_name} should return 400/422, got {response.status_code}"
            print(f"   ✅ {test_name}: {response.status_code}")
        
        # Test non-existent resources
        not_found_tests = [
            ("Non-existent Kid", "/v1/kids/99999", "GET"),
            ("Non-existent Event", "/v1/events/99999", "GET"),
            ("Non-existent Event Update", "/v1/events/99999", "PATCH")
        ]
        
        for test_name, endpoint, method in not_found_tests:
            if method == "PATCH":
                response = self.session.patch(f"{self.base_url}{endpoint}", json={"title": "Test"})
            else:
                response = self.session.get(f"{self.base_url}{endpoint}")
            assert response.status_code == 404, f"{test_name} should return 404, got {response.status_code}"
            print(f"   ✅ {test_name}: {response.status_code}")
        
        # Test large data sets
        large_kid_data = {
            "name": "A" * 1000,  # Very long name
            "color": "#ff0000",
            "avatar": "https://example.com/" + "a" * 1000  # Very long URL
        }
        response = self.session.post(f"{self.base_url}/v1/kids/", json=large_kid_data)
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 201, 400, 422], f"Large data test should handle gracefully, got {response.status_code}"
        if response.status_code in [200, 201]:
            # Clean up if it succeeded
            kid = response.json()
            self.session.delete(f"{self.base_url}/v1/kids/{kid['id']}")
        
        print("✅ Error handling and edge cases test passed")
    
    def test_real_time_updates(self):
        """Test real-time update performance (≤10s)"""
        print("\n🔄 Testing Real-time Updates...")
        
        # Get initial version
        response = self.session.get(f"{self.base_url}/v1/events/version")
        assert response.status_code == 200
        initial_version = response.json()["last_updated"]
        
        # Create a new event
        event_data = {
            "title": "Real-time Test Event",
            "location": "Real-time Location",
            "start_utc": "2025-09-15T10:00:00Z",
            "end_utc": "2025-09-15T11:00:00Z",
            "kid_ids": [str(self.test_data["kids"][0]["id"])],
            "category": "family",
            "source": "manual"
        }
        
        start_time = time.time()
        response = self.session.post(f"{self.base_url}/v1/events/", json=event_data)
        assert response.status_code == 201
        created_event = response.json()
        
        # Poll for version changes
        max_wait_time = 10  # 10 seconds
        poll_interval = 0.5  # 0.5 seconds
        version_updated = False
        
        while time.time() - start_time < max_wait_time:
            response = self.session.get(f"{self.base_url}/v1/events/version")
            assert response.status_code == 200
            current_version = response.json()["last_updated"]
            
            if current_version != initial_version:
                version_updated = True
                break
            
            time.sleep(poll_interval)
        
        end_time = time.time()
        update_time = end_time - start_time
        
        assert version_updated, "Version should have updated within 10 seconds"
        assert update_time <= 10, f"Real-time update took {update_time:.2f}s, exceeds 10s limit"
        
        print(f"⏱️  Real-time update detected in {update_time:.2f}s")
        
        # Clean up
        self.session.delete(f"{self.base_url}/v1/events/{created_event['id']}")
        
        print("✅ Real-time updates test passed")
    
    def run_comprehensive_tests(self):
        """Run all comprehensive end-to-end tests"""
        print("🧪 Starting Comprehensive End-to-End Tests")
        print("=" * 60)
        
        try:
            self.setup_test_data()
            
            self.test_complete_user_workflow()
            self.test_performance_requirements()
            self.test_rrule_complexity()
            self.test_concurrent_operations()
            self.test_error_handling_and_edge_cases()
            self.test_real_time_updates()
            
            print("\n" + "=" * 60)
            print("🎉 All comprehensive end-to-end tests passed!")
            
            # Print performance summary
            if self.performance_metrics:
                print("\n📊 Performance Summary:")
                for operation, duration in self.performance_metrics.items():
                    print(f"   {operation}: {duration:.2f}ms")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            return False
            
        finally:
            self.cleanup_test_data()


def test_e2e_comprehensive():
    """Pytest wrapper for comprehensive E2E tests"""
    suite = E2ETestSuite()
    assert suite.run_comprehensive_tests()


if __name__ == "__main__":
    suite = E2ETestSuite()
    success = suite.run_comprehensive_tests()
    exit(0 if success else 1)
