#!/usr/bin/env python3
"""
Simple test script to verify the basic setup is working
"""

import requests
import time
import sys

def test_api_health():
    """Test if the API is responding"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ API health check passed")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API - is it running?")
        return False

def test_database_connection():
    """Test if the database is accessible"""
    try:
        response = requests.get("http://localhost:8000/v1/kids")
        if response.status_code == 200:
            print("✅ Database connection working")
            return True
        else:
            print(f"❌ Database connection failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API")
        return False

def main():
    print("🧪 Testing Family Calendar Setup...")
    print("=" * 40)
    
    # Wait a bit for services to start
    print("⏳ Waiting for services to start...")
    time.sleep(5)
    
    # Test API health
    api_ok = test_api_health()
    
    # Test database connection
    db_ok = test_database_connection()
    
    print("=" * 40)
    if api_ok and db_ok:
        print("🎉 All tests passed! Setup is working correctly.")
        return 0
    else:
        print("�� Some tests failed. Please check the setup.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 