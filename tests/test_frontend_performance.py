#!/usr/bin/env python3
"""
Frontend Performance and Compatibility Test Suite
Tests frontend rendering, browser compatibility, and user experience
"""

import pytest
import requests
import time
import json
from datetime import datetime, timezone
from typing import Dict, List, Any
import statistics


class FrontendPerformanceTest:
    """Frontend performance and compatibility test suite"""
    
    def __init__(self, base_url: str = "http://localhost:8088"):
        self.base_url = base_url
        self.session = requests.Session()
        self.performance_metrics = {}
    
    def test_frontend_availability(self):
        """Test that frontend files are accessible"""
        print("\n🌐 Testing Frontend Availability...")
        
        frontend_files = [
            "/frontend/wall.html",
            "/frontend/test_enhanced_features.html",
            "/frontend/test_overlapping_events.html",
            "/frontend/test_real_time_updates.html",
            "/frontend/test_realtime_integration.html",
            "/frontend/test_wall_display.html",
            "/frontend/verify_enhanced_features.html"
        ]
        
        for file_path in frontend_files:
            response = self.session.get(f"{self.base_url}{file_path}")
            assert response.status_code == 200, f"Frontend file {file_path} not accessible"
            assert "text/html" in response.headers.get("content-type", ""), f"Frontend file {file_path} not HTML"
            print(f"   ✅ {file_path}: Accessible")
        
        print("✅ Frontend availability test passed")
    
    def test_api_endpoints_for_frontend(self):
        """Test that all API endpoints used by frontend are working"""
        print("\n🔌 Testing API Endpoints for Frontend...")
        
        # Test endpoints that frontend uses
        api_endpoints = [
            ("Health Check", "/health"),
            ("Kids API", "/v1/kids/"),
            ("Events API", "/v1/events/"),
            ("Events with Date Range", "/v1/events/?start=2025-09-01T00:00:00Z&end=2025-09-07T23:59:59Z"),
            ("Events Version", "/v1/events/version"),
            ("Weekly Events", "/v1/events/weekly/?week_start=2025-09-01T00:00:00Z"),
            ("Daily Events", "/v1/events/daily/?day=2025-09-05T00:00:00Z"),
            ("Expanded Events", "/v1/events/expanded/")
        ]
        
        for endpoint_name, endpoint_path in api_endpoints:
            response = self.session.get(f"{self.base_url}{endpoint_path}")
            assert response.status_code == 200, f"API endpoint {endpoint_name} failed: {response.status_code}"
            
            # Test response time
            start_time = time.time()
            response = self.session.get(f"{self.base_url}{endpoint_path}")
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            assert response_time <= 300, f"API endpoint {endpoint_name} too slow: {response_time:.2f}ms"
            print(f"   ✅ {endpoint_name}: {response_time:.2f}ms")
        
        print("✅ API endpoints for frontend test passed")
    
    def test_frontend_data_loading_simulation(self):
        """Simulate frontend data loading sequence and measure performance"""
        print("\n📊 Testing Frontend Data Loading Simulation...")
        
        # Simulate the exact sequence that frontend uses
        loading_sequence = [
            ("Load Kids", lambda: self.session.get(f"{self.base_url}/v1/kids/")),
            ("Load Events for Current Week", lambda: self.session.get(f"{self.base_url}/v1/events/?start=2025-09-01T00:00:00Z&end=2025-09-07T23:59:59Z")),
            ("Check for Updates", lambda: self.session.get(f"{self.base_url}/v1/events/version"))
        ]
        
        total_start_time = time.time()
        individual_times = []
        
        for step_name, step_func in loading_sequence:
            start_time = time.time()
            response = step_func()
            end_time = time.time()
            
            step_time = (end_time - start_time) * 1000
            individual_times.append(step_time)
            
            assert response.status_code == 200, f"Frontend loading step {step_name} failed"
            assert step_time <= 300, f"Frontend loading step {step_name} too slow: {step_time:.2f}ms"
            
            print(f"   ⏱️  {step_name}: {step_time:.2f}ms")
        
        total_end_time = time.time()
        total_time = (total_end_time - total_start_time) * 1000
        
        # Test that total loading time is within acceptable limits
        assert total_time <= 1000, f"Total frontend loading time {total_time:.2f}ms exceeds 1s limit"
        
        # Test that individual steps are fast enough
        avg_time = statistics.mean(individual_times)
        max_time = max(individual_times)
        
        print(f"   📈 Total Loading Time: {total_time:.2f}ms")
        print(f"   📈 Average Step Time: {avg_time:.2f}ms")
        print(f"   📈 Maximum Step Time: {max_time:.2f}ms")
        
        self.performance_metrics["frontend_loading"] = {
            "total_time": total_time,
            "average_step_time": avg_time,
            "max_step_time": max_time,
            "individual_times": individual_times
        }
        
        print("✅ Frontend data loading simulation test passed")
    
    def test_concurrent_frontend_requests(self):
        """Test concurrent requests that might happen in frontend"""
        print("\n🔄 Testing Concurrent Frontend Requests...")
        
        import threading
        import queue
        
        results = queue.Queue()
        errors = queue.Queue()
        
        def concurrent_request(request_id):
            try:
                # Simulate different types of requests that might happen concurrently
                requests_to_make = [
                    ("Kids", f"{self.base_url}/v1/kids/"),
                    ("Events", f"{self.base_url}/v1/events/"),
                    ("Version", f"{self.base_url}/v1/events/version")
                ]
                
                for req_name, url in requests_to_make:
                    start_time = time.time()
                    response = self.session.get(url)
                    end_time = time.time()
                    
                    response_time = (end_time - start_time) * 1000
                    
                    if response.status_code != 200:
                        errors.put(f"Request {request_id} {req_name}: HTTP {response.status_code}")
                        return
                    
                    if response_time > 500:
                        errors.put(f"Request {request_id} {req_name}: Too slow {response_time:.2f}ms")
                        return
                
                results.put(f"Request {request_id}: Success")
                
            except Exception as e:
                errors.put(f"Request {request_id}: Exception - {str(e)}")
        
        # Run 10 concurrent request sequences
        threads = []
        for i in range(10):
            thread = threading.Thread(target=concurrent_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = results.qsize()
        error_count = errors.qsize()
        
        print(f"   📊 Concurrent Requests Results:")
        print(f"      Successful: {success_count}")
        print(f"      Errors: {error_count}")
        
        # Print any errors
        while not errors.empty():
            print(f"      ❌ {errors.get()}")
        
        assert error_count == 0, f"Concurrent frontend requests failed: {error_count} errors"
        assert success_count == 10, f"Expected 10 successful request sequences, got {success_count}"
        
        print("✅ Concurrent frontend requests test passed")
    
    def test_frontend_error_handling(self):
        """Test frontend error handling scenarios"""
        print("\n🚨 Testing Frontend Error Handling...")
        
        # Test scenarios that frontend should handle gracefully
        error_scenarios = [
            ("Invalid Date Range", "/v1/events/?start=invalid-date&end=invalid-date"),
            ("Future Date Range", "/v1/events/?start=2030-01-01T00:00:00Z&end=2030-01-07T23:59:59Z"),
            ("Very Large Date Range", "/v1/events/?start=2020-01-01T00:00:00Z&end=2030-12-31T23:59:59Z"),
            ("Invalid Week Start", "/v1/events/weekly/?week_start=invalid-date"),
            ("Invalid Day", "/v1/events/daily/?day=invalid-date")
        ]
        
        for scenario_name, endpoint in error_scenarios:
            response = self.session.get(f"{self.base_url}{endpoint}")
            
            # Frontend should handle these gracefully (either 200 with empty results or 400/422)
            assert response.status_code in [200, 400, 422], f"Error scenario {scenario_name} should be handled gracefully, got {response.status_code}"
            
            if response.status_code == 200:
                # Should return empty results or valid error response
                data = response.json()
                assert isinstance(data, (list, dict)), f"Error scenario {scenario_name} should return valid JSON"
            
            print(f"   ✅ {scenario_name}: {response.status_code}")
        
        print("✅ Frontend error handling test passed")
    
    def test_frontend_cors_headers(self):
        """Test CORS headers for frontend access"""
        print("\n🌐 Testing CORS Headers...")
        
        # Test CORS preflight request
        headers = {
            "Origin": "http://localhost:8088",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = self.session.options(f"{self.base_url}/v1/kids/", headers=headers)
        
        # Check CORS headers
        cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers"
        ]
        
        for header in cors_headers:
            assert header in response.headers, f"CORS header {header} missing"
            print(f"   ✅ {header}: {response.headers[header]}")
        
        print("✅ CORS headers test passed")
    
    def test_frontend_static_files(self):
        """Test static file serving for frontend"""
        print("\n📁 Testing Static File Serving...")
        
        # Test that static files are served with correct headers
        static_files = [
            "/frontend/wall.html"
        ]
        
        for file_path in static_files:
            response = self.session.get(f"{self.base_url}{file_path}")
            assert response.status_code == 200, f"Static file {file_path} not accessible"
            
            # Check content type
            content_type = response.headers.get("content-type", "")
            assert "text/html" in content_type, f"Static file {file_path} wrong content type: {content_type}"
            
            # Check cache headers (should be present for performance)
            cache_control = response.headers.get("cache-control", "")
            etag = response.headers.get("etag", "")
            last_modified = response.headers.get("last-modified", "")
            
            print(f"   ✅ {file_path}:")
            print(f"      Content-Type: {content_type}")
            print(f"      Cache-Control: {cache_control}")
            print(f"      ETag: {etag}")
            print(f"      Last-Modified: {last_modified}")
        
        print("✅ Static file serving test passed")
    
    def run_frontend_tests(self):
        """Run all frontend performance and compatibility tests"""
        print("🧪 Starting Frontend Performance and Compatibility Tests")
        print("=" * 60)
        
        try:
            self.test_frontend_availability()
            self.test_api_endpoints_for_frontend()
            self.test_frontend_data_loading_simulation()
            self.test_concurrent_frontend_requests()
            self.test_frontend_error_handling()
            self.test_frontend_cors_headers()
            self.test_frontend_static_files()
            
            print("\n" + "=" * 60)
            print("🎉 All frontend performance and compatibility tests passed!")
            
            # Print performance summary
            if self.performance_metrics:
                print("\n📊 Frontend Performance Summary:")
                for metric, data in self.performance_metrics.items():
                    if isinstance(data, dict):
                        print(f"   {metric}:")
                        for key, value in data.items():
                            if key != "individual_times":
                                print(f"      {key}: {value:.2f}ms")
                    else:
                        print(f"   {metric}: {data:.2f}ms")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Frontend test failed: {str(e)}")
            return False


def test_frontend_performance():
    """Pytest wrapper for frontend performance tests"""
    suite = FrontendPerformanceTest()
    assert suite.run_frontend_tests()


if __name__ == "__main__":
    suite = FrontendPerformanceTest()
    success = suite.run_frontend_tests()
    exit(0 if success else 1)
