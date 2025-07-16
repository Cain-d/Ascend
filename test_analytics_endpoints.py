#!/usr/bin/env python3
"""
Test script for analytics API endpoints
"""

import requests
import json
from datetime import datetime, timedelta

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword"

def create_test_user():
    """Create a test user"""
    response = requests.post(f"{BASE_URL}/create_user", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })
    return response.status_code in [200, 400]  # 400 if user already exists

def login_and_get_token():
    """Login and get access token"""
    response = requests.post(f"{BASE_URL}/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_analytics_endpoints():
    """Test all analytics endpoints"""
    print("Testing Analytics API Endpoints")
    print("=" * 40)
    
    # Create test user and login
    print("1. Creating test user...")
    create_test_user()
    
    print("2. Logging in...")
    token = login_and_get_token()
    if not token:
        print("❌ Failed to login")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test trends endpoint
    print("\n3. Testing /analytics/trends endpoint...")
    response = requests.get(f"{BASE_URL}/analytics/trends", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 400:
        print(f"   Expected insufficient data error: {response.json().get('message', 'No message')}")
    elif response.status_code == 200:
        print(f"   Success: Got trends data")
    else:
        print(f"   Unexpected response: {response.text}")
    
    # Test predictions endpoint
    print("\n4. Testing /analytics/predictions endpoint...")
    response = requests.get(f"{BASE_URL}/analytics/predictions", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 400:
        print(f"   Expected insufficient data error: {response.json().get('message', 'No message')}")
    elif response.status_code == 200:
        print(f"   Success: Got predictions data")
    else:
        print(f"   Unexpected response: {response.text}")
    
    # Test recommendations endpoint
    print("\n5. Testing /analytics/recommendations endpoint...")
    response = requests.get(f"{BASE_URL}/analytics/recommendations", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 400:
        print(f"   Expected insufficient data error: {response.json().get('message', 'No message')}")
    elif response.status_code == 200:
        print(f"   Success: Got recommendations data")
    else:
        print(f"   Unexpected response: {response.text}")
    
    # Test insights endpoint
    print("\n6. Testing /analytics/insights endpoint...")
    response = requests.get(f"{BASE_URL}/analytics/insights", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 400:
        print(f"   Expected insufficient data error: {response.json().get('message', 'No message')}")
    elif response.status_code == 200:
        print(f"   Success: Got insights data")
    else:
        print(f"   Unexpected response: {response.text}")
    
    # Test invalid goal type
    print("\n7. Testing invalid goal type...")
    response = requests.get(f"{BASE_URL}/analytics/recommendations?goal_type=invalid", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 400:
        error_data = response.json()
        if error_data.get("error") == "invalid_goal":
            print(f"   ✅ Correctly rejected invalid goal type")
        else:
            print(f"   Expected invalid_goal error: {error_data}")
    
    print("\n" + "=" * 40)
    print("Analytics API endpoints test completed!")

if __name__ == "__main__":
    test_analytics_endpoints()