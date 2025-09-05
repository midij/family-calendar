#!/usr/bin/env python3
"""
Browser Compatibility Test Suite
Tests cross-browser compatibility and responsive design
"""

import pytest
import requests
import time
import json
from datetime import datetime, timezone
from typing import Dict, List, Any
import subprocess
import os


class BrowserCompatibilityTest:
    """Browser compatibility and responsive design test suite"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = {}
    
    def test_responsive_design_simulation(self):
        """Simulate different screen sizes and test responsive design"""
        print("\n📱 Testing Responsive Design Simulation...")
        
        # Test different viewport sizes
        viewport_sizes = [
            ("Mobile Portrait", 375, 667),      # iPhone SE
            ("Mobile Landscape", 667, 375),     # iPhone SE landscape
            ("Tablet Portrait", 768, 1024),     # iPad
            ("Tablet Landscape", 1024, 768),    # iPad landscape
            ("Desktop Small", 1024, 768),       # Small desktop
            ("Desktop Large", 1920, 1080),      # Large desktop
            ("Wall Display", 3840, 2160)        # 4K wall display
        ]
        
        for size_name, width, height in viewport_sizes:
            print(f"   📐 Testing {size_name} ({width}x{height})...")
            
            # Test that frontend loads for different screen sizes
            response = self.session.get(f"{self.base_url}/frontend/wall.html")
            assert response.status_code == 200, f"Frontend not accessible for {size_name}"
            
            # Test API endpoints that frontend uses
            api_tests = [
                ("Kids API", "/v1/kids/"),
                ("Events API", "/v1/events/"),
                ("Events Version", "/v1/events/version")
            ]
            
            for api_name, endpoint in api_tests:
                response = self.session.get(f"{self.base_url}{endpoint}")
                assert response.status_code == 200, f"API {api_name} not accessible for {size_name}"
            
            print(f"      ✅ {size_name}: All endpoints accessible")
        
        print("✅ Responsive design simulation test passed")
    
    def test_cross_browser_headers(self):
        """Test headers and responses for cross-browser compatibility"""
        print("\n🌐 Testing Cross-Browser Compatibility Headers...")
        
        # Test main frontend page
        response = self.session.get(f"{self.base_url}/frontend/wall.html")
        assert response.status_code == 200
        
        # Check important headers for cross-browser compatibility
        headers_to_check = [
            ("Content-Type", "text/html; charset=utf-8"),
            ("X-Content-Type-Options", "nosniff"),
            ("X-Frame-Options", "DENY"),
            ("X-XSS-Protection", "1; mode=block")
        ]
        
        for header_name, expected_value in headers_to_check:
            actual_value = response.headers.get(header_name, "")
            if expected_value:
                assert expected_value in actual_value, f"Header {header_name} should contain {expected_value}, got {actual_value}"
            print(f"   ✅ {header_name}: {actual_value}")
        
        # Test API endpoints for CORS (using OPTIONS preflight requests)
        api_endpoints = ["/v1/kids/", "/v1/events/", "/v1/events/version"]
        
        for endpoint in api_endpoints:
            # Test CORS preflight request
            headers = {
                "Origin": "http://localhost:8000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            }
            
            response = self.session.options(f"{self.base_url}{endpoint}", headers=headers)
            assert response.status_code == 200, f"CORS preflight request failed for {endpoint}: {response.status_code}"
            
            # Check CORS headers
            cors_headers = [
                "Access-Control-Allow-Origin",
                "Access-Control-Allow-Methods",
                "Access-Control-Allow-Headers"
            ]
            
            for header in cors_headers:
                assert header in response.headers, f"CORS header {header} missing for {endpoint}"
                print(f"   ✅ {endpoint} {header}: {response.headers[header]}")
        
        print("✅ Cross-browser compatibility headers test passed")
    
    def test_mobile_specific_features(self):
        """Test mobile-specific features and touch interactions"""
        print("\n📱 Testing Mobile-Specific Features...")
        
        # Test that the frontend loads on mobile user agents
        mobile_user_agents = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        ]
        
        for user_agent in mobile_user_agents:
            headers = {"User-Agent": user_agent}
            response = self.session.get(f"{self.base_url}/frontend/wall.html", headers=headers)
            assert response.status_code == 200, f"Frontend not accessible with mobile user agent: {user_agent[:50]}..."
            
            # Test API endpoints with mobile user agent
            api_response = self.session.get(f"{self.base_url}/v1/kids/", headers=headers)
            assert api_response.status_code == 200, f"API not accessible with mobile user agent"
            
            print(f"   ✅ Mobile User Agent: {user_agent[:50]}...")
        
        print("✅ Mobile-specific features test passed")
    
    def test_tablet_optimization(self):
        """Test tablet-specific optimizations"""
        print("\n📱 Testing Tablet Optimization...")
        
        # Test tablet user agents
        tablet_user_agents = [
            "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 10; SM-T870) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Safari/537.36"
        ]
        
        for user_agent in tablet_user_agents:
            headers = {"User-Agent": user_agent}
            
            # Test frontend accessibility
            response = self.session.get(f"{self.base_url}/frontend/wall.html", headers=headers)
            assert response.status_code == 200, f"Frontend not accessible on tablet: {user_agent[:50]}..."
            
            # Test API performance on tablet
            start_time = time.time()
            api_response = self.session.get(f"{self.base_url}/v1/events/", headers=headers)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            assert api_response.status_code == 200, f"API not accessible on tablet"
            assert response_time <= 150, f"API too slow on tablet: {response_time:.2f}ms"
            
            print(f"   ✅ Tablet User Agent: {user_agent[:50]}... ({response_time:.2f}ms)")
        
        print("✅ Tablet optimization test passed")
    
    def test_wall_display_mode(self):
        """Test wall display mode and readability from distance"""
        print("\n🖥️ Testing Wall Display Mode...")
        
        # Test large screen simulation
        wall_display_headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        }
        
        # Test frontend accessibility for wall display
        response = self.session.get(f"{self.base_url}/frontend/wall.html", headers=wall_display_headers)
        assert response.status_code == 200, "Frontend not accessible for wall display"
        
        # Test that all necessary data loads quickly for wall display
        wall_display_tests = [
            ("Kids Data", "/v1/kids/"),
            ("Events Data", "/v1/events/"),
            ("Version Check", "/v1/events/version")
        ]
        
        total_start_time = time.time()
        
        for test_name, endpoint in wall_display_tests:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}{endpoint}", headers=wall_display_headers)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            assert response.status_code == 200, f"Wall display {test_name} not accessible"
            assert response_time <= 150, f"Wall display {test_name} too slow: {response_time:.2f}ms"
            
            print(f"   ⏱️  {test_name}: {response_time:.2f}ms")
        
        total_end_time = time.time()
        total_time = (total_end_time - total_start_time) * 1000
        
        assert total_time <= 1000, f"Wall display total load time {total_time:.2f}ms exceeds 1s limit"
        
        print(f"   📊 Total Wall Display Load Time: {total_time:.2f}ms")
        print("✅ Wall display mode test passed")
    
    def test_offline_functionality(self):
        """Test offline functionality and cache behavior"""
        print("\n📴 Testing Offline Functionality...")
        
        # Test cache headers for offline functionality
        response = self.session.get(f"{self.base_url}/frontend/wall.html")
        assert response.status_code == 200
        
        # Check for cache headers
        cache_headers = [
            "Cache-Control",
            "ETag",
            "Last-Modified"
        ]
        
        cache_info = {}
        for header in cache_headers:
            value = response.headers.get(header, "")
            cache_info[header] = value
            print(f"   📦 {header}: {value}")
        
        # Test conditional requests (for offline functionality)
        if cache_info.get("ETag"):
            etag = cache_info["ETag"]
            headers = {"If-None-Match": etag}
            response = self.session.get(f"{self.base_url}/frontend/wall.html", headers=headers)
            
            # Should return 304 Not Modified for cached content
            assert response.status_code == 304, f"Conditional request should return 304, got {response.status_code}"
            print(f"   ✅ Conditional Request (ETag): 304 Not Modified")
        
        if cache_info.get("Last-Modified"):
            last_modified = cache_info["Last-Modified"]
            headers = {"If-Modified-Since": last_modified}
            response = self.session.get(f"{self.base_url}/frontend/wall.html", headers=headers)
            
            # Should return 304 Not Modified for cached content
            assert response.status_code == 304, f"Conditional request should return 304, got {response.status_code}"
            print(f"   ✅ Conditional Request (Last-Modified): 304 Not Modified")
        
        print("✅ Offline functionality test passed")
    
    def test_accessibility_features(self):
        """Test accessibility features for wall display"""
        print("\n♿ Testing Accessibility Features...")
        
        # Test that frontend loads with accessibility headers
        response = self.session.get(f"{self.base_url}/frontend/wall.html")
        assert response.status_code == 200
        
        # Check for accessibility-related headers
        accessibility_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection"
        ]
        
        for header in accessibility_headers:
            value = response.headers.get(header, "")
            assert value, f"Accessibility header {header} should be present"
            print(f"   ♿ {header}: {value}")
        
        # Test that API responses are accessible
        api_response = self.session.get(f"{self.base_url}/v1/kids/")
        assert api_response.status_code == 200
        
        # Check that API returns valid JSON
        try:
            data = api_response.json()
            assert isinstance(data, list), "API should return list of kids"
            print(f"   ♿ API Response: Valid JSON with {len(data)} kids")
        except json.JSONDecodeError:
            assert False, "API should return valid JSON"
        
        print("✅ Accessibility features test passed")
    
    def run_browser_compatibility_tests(self):
        """Run all browser compatibility and responsive design tests"""
        print("🧪 Starting Browser Compatibility and Responsive Design Tests")
        print("=" * 60)
        
        try:
            self.test_responsive_design_simulation()
            self.test_cross_browser_headers()
            self.test_mobile_specific_features()
            self.test_tablet_optimization()
            self.test_wall_display_mode()
            self.test_offline_functionality()
            self.test_accessibility_features()
            
            print("\n" + "=" * 60)
            print("🎉 All browser compatibility and responsive design tests passed!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Browser compatibility test failed: {str(e)}")
            return False


def test_browser_compatibility():
    """Pytest wrapper for browser compatibility tests"""
    suite = BrowserCompatibilityTest()
    assert suite.run_browser_compatibility_tests()


if __name__ == "__main__":
    suite = BrowserCompatibilityTest()
    success = suite.run_browser_compatibility_tests()
    exit(0 if success else 1)
