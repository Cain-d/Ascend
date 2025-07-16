#!/usr/bin/env python3
"""
Simple test to verify analytics endpoints are accessible
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints_without_auth():
    """Test that endpoints exist and return proper authentication errors"""
    print("Testing Analytics API Endpoints (without auth)")
    print("=" * 50)
    
    endpoints = [
        "/analytics/trends",
        "/analytics/predictions", 
        "/analytics/recommendations",
        "/analytics/insights"
    ]
    
    for endpoint in endpoints:
        print(f"\nTesting {endpoint}...")
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 401:
                print(f"   ✅ Correctly requires authentication")
            elif response.status_code == 422:
                print(f"   ✅ Endpoint exists (validation error expected)")
            else:
                print(f"   Response: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Server not running or connection failed")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Test root endpoint to verify server is running
    print(f"\nTesting root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Server is running: {response.json()}")
    except Exception as e:
        print(f"   ❌ Server connection failed: {e}")

if __name__ == "__main__":
    test_endpoints_without_auth()