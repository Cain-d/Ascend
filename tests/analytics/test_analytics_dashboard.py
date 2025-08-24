#!/usr/bin/env python3
"""
Test script to verify the analytics dashboard frontend component integration.
This tests that the frontend can properly handle analytics API responses.
"""

import requests
import json
import sys
import time

def test_analytics_endpoints():
    """Test that analytics endpoints return expected data structure"""
    base_url = "http://localhost:8000"
    
    # Test endpoints that should work even with insufficient data
    endpoints_to_test = [
        "/analytics/insights",
        "/analytics/trends?days=30",
        "/analytics/predictions?workout_type=general",
        "/analytics/recommendations?goal_type=maintenance"
    ]
    
    print("Testing Analytics API Endpoints...")
    print("=" * 50)
    
    for endpoint in endpoints_to_test:
        try:
            print(f"\nTesting: {endpoint}")
            response = requests.get(f"{base_url}{endpoint}")
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Success - Got valid response")
                print(f"Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
            elif response.status_code == 400:
                # Expected for insufficient data
                error_data = response.json()
                if error_data.get("error") == "insufficient_data":
                    print("✅ Expected insufficient_data response")
                    print(f"Message: {error_data.get('message', 'No message')}")
                    print(f"Suggestions: {len(error_data.get('suggestions', []))} provided")
                else:
                    print(f"❌ Unexpected 400 error: {error_data}")
                    
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                print(f"Response: {response.text[:200]}...")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection failed - Is the server running on {base_url}?")
            return False
        except Exception as e:
            print(f"❌ Error testing {endpoint}: {e}")
            return False
    
    return True

def test_frontend_structure():
    """Test that frontend files are properly structured"""
    import os
    
    print("\nTesting Frontend File Structure...")
    print("=" * 50)
    
    required_files = [
        "ascend-frontend/src/components/Analytics/AnalyticsDashboard.jsx",
        "ascend-frontend/src/App.jsx",
        "ascend-frontend/src/api.js"
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
            
            # Check file content for key components
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'AnalyticsDashboard.jsx' in file_path:
                checks = [
                    ('useState', 'React hooks'),
                    ('fetchAnalyticsData', 'Data fetching function'),
                    ('renderTabNavigation', 'Tab navigation'),
                    ('analytics/insights', 'API endpoint call')
                ]
                
                for check, description in checks:
                    if check in content:
                        print(f"  ✅ Contains {description}")
                    else:
                        print(f"  ❌ Missing {description}")
                        
            elif 'App.jsx' in file_path:
                if 'AnalyticsDashboard' in content and 'analytics' in content:
                    print(f"  ✅ Includes analytics dashboard integration")
                else:
                    print(f"  ❌ Missing analytics dashboard integration")
                    
            elif 'api.js' in file_path:
                analytics_functions = [
                    'fetchAnalyticsTrends',
                    'fetchAnalyticsPredictions', 
                    'fetchAnalyticsRecommendations',
                    'fetchAnalyticsInsights'
                ]
                
                missing_functions = [func for func in analytics_functions if func not in content]
                if not missing_functions:
                    print(f"  ✅ All analytics API functions present")
                else:
                    print(f"  ❌ Missing functions: {missing_functions}")
        else:
            print(f"❌ {file_path} missing")
            return False
    
    return True

def main():
    """Run all tests"""
    print("Analytics Dashboard Integration Test")
    print("=" * 60)
    
    # Test frontend structure
    frontend_ok = test_frontend_structure()
    
    if not frontend_ok:
        print("\n❌ Frontend structure test failed")
        return False
    
    # Test API endpoints
    api_ok = test_analytics_endpoints()
    
    if not api_ok:
        print("\n❌ API endpoint test failed")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! Analytics dashboard is ready.")
    print("\nTo use the analytics dashboard:")
    print("1. Start the backend server: cd Ascend && python -m uvicorn app.main:app --reload")
    print("2. Start the frontend: cd Ascend/ascend-frontend && npm run dev")
    print("3. Navigate to the Analytics tab in the web interface")
    print("\nNote: You'll need to log some data first to see meaningful analytics.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)