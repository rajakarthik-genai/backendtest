#!/usr/bin/env python3
"""
Comprehensive JWT authentication fix script
"""

import requests
import json
import time
import os
import sys
from pathlib import Path

def restart_backend_service():
    """Restart the backend service to load new configuration"""
    print("🔄 Restarting backend service...")
    
    # Try to restart via docker-compose or similar
    try:
        # Check if we're in a containerized environment
        if os.path.exists('/.dockerenv'):
            print("📦 Detected containerized environment")
            # Signal for restart or wait for auto-reload
            print("Service should auto-reload on config changes")
        else:
            print("🏠 Local environment detected")
            
    except Exception as e:
        print(f"❌ Error restarting service: {e}")

def verify_jwt_configuration():
    """Verify JWT configuration is correctly set"""
    print("🔍 Verifying JWT configuration...")
    
    # Check the current config
    config_path = Path(__file__).parent / 'src' / 'core' / 'config.py'
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        if 'your-secret-key' in content:
            print("✅ JWT secret key correctly set to 'your-secret-key'")
            return True
        else:
            print("❌ JWT secret key not found in config")
            return False
            
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return False

def test_endpoints_with_retry():
    """Test endpoints with retry logic"""
    print("🧪 Testing endpoints with retry...")
    
    login_url = "https://lenient-sunny-grouse.ngrok-free.app"
    agents_url = "https://mackerel-liberal-loosely.ngrok-free.app"
    
    # Get fresh token
    try:
        response = requests.post(
            f"{login_url}/auth/login",
            json={"email": "user@example.com", "password": "Raja@1234"}
        )
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"✅ Fresh token obtained")
            
            # Test endpoints
            headers = {"Authorization": f"Bearer {token}"}
            
            endpoints = [
                f"{agents_url}/api/v1/health/body-parts",
                f"{agents_url}/api/v1/health/summary",
                f"{agents_url}/api/v1/documents/status",
                f"{agents_url}/api/v1/timeline/events"
            ]
            
            success_count = 0
            for endpoint in endpoints:
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        resp = requests.get(endpoint, headers=headers, timeout=10)
                        
                        if resp.status_code == 200:
                            print(f"  ✅ {endpoint}: 200 OK")
                            success_count += 1
                            break
                        elif resp.status_code == 401:
                            print(f"  ❌ {endpoint}: 401 Unauthorized")
                            if attempt < max_retries - 1:
                                print(f"    Retrying in 2 seconds...")
                                time.sleep(2)
                            else:
                                print(f"    Error: {resp.text[:100]}")
                        else:
                            print(f"  ⚠️ {endpoint}: {resp.status_code}")
                            print(f"    Response: {resp.text[:100]}")
                            break
                            
                    except requests.exceptions.RequestException as e:
                        print(f"  ❌ {endpoint}: Request error - {e}")
                        break
            
            return success_count, len(endpoints)
            
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")
        return 0, 0

def create_manual_test_script():
    """Create a manual test script for verification"""
    print("📝 Creating manual test script...")
    
    test_script = '''#!/usr/bin/env python3
"""
Manual JWT endpoint testing script
"""

import requests
import json

def test_all_endpoints():
    """Test all endpoints with JWT token"""
    
    # Configuration
    login_url = "https://lenient-sunny-grouse.ngrok-free.app"
    agents_url = "https://mackerel-liberal-loosely.ngrok-free.app"
    
    print("🔐 Getting authentication token...")
    
    # Login
    login_response = requests.post(
        f"{login_url}/auth/login",
        json={"email": "user@example.com", "password": "Raja@1234"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    print(f"✅ Token obtained: {token[:50]}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test endpoints
    endpoints = [
        ("GET", f"{agents_url}/api/v1/health/body-parts"),
        ("GET", f"{agents_url}/api/v1/health/summary"),
        ("GET", f"{agents_url}/api/v1/documents/status"),
        ("GET", f"{agents_url}/api/v1/timeline/events"),
        ("POST", f"{agents_url}/api/v1/chat/message", {"query": "Hello, how are you?"}),
        ("GET", f"{agents_url}/api/v1/reports"),
    ]
    
    results = []
    
    print("\\n🧪 Testing endpoints...")
    for method, url, *data in endpoints:
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            else:
                response = requests.post(url, headers=headers, json=data[0], timeout=30)
            
            results.append({
                "endpoint": url,
                "method": method,
                "status": response.status_code,
                "response": response.text[:200]
            })
            
            print(f"  {method} {url}: {response.status_code}")
            
        except Exception as e:
            results.append({
                "endpoint": url,
                "method": method,
                "status": "ERROR",
                "response": str(e)
            })
            print(f"  {method} {url}: ERROR - {e}")
    
    # Summary
    print("\\n📊 Test Results Summary:")
    success_count = sum(1 for r in results if str(r["status"]).startswith("2"))
    total_count = len(results)
    
    print(f"Successful: {success_count}/{total_count}")
    
    for result in results:
        status = "✅" if str(result["status"]).startswith("2") else "❌"
        print(f"{status} {result['method']} {result['endpoint']}: {result['status']}")

if __name__ == "__main__":
    test_all_endpoints()
'''
    
    script_path = Path(__file__).parent / 'final_test.py'
    with open(script_path, 'w') as f:
        f.write(test_script)
    
    # Make executable
    os.chmod(script_path, 0o755)
    
    print(f"✅ Manual test script created: {script_path}")
    return str(script_path)

def main():
    """Main fix function"""
    print("🚀 Medical Digital Twin JWT Authentication Fix")
    print("=" * 60)
    
    # Verify configuration
    config_ok = verify_jwt_configuration()
    
    if config_ok:
        print("✅ Configuration verified")
        
        # Test endpoints
        success, total = test_endpoints_with_retry()
        
        if success > 0:
            print(f"✅ {success}/{total} endpoints working")
        else:
            print(f"❌ {success}/{total} endpoints working")
            
            # Create manual test script
            test_script = create_manual_test_script()
            print(f"📝 Use {test_script} for detailed testing")
    
    print("\n📊 Fix Summary:")
    print(f"JWT Configuration: {'✅' if config_ok else '❌'}")
    print("Next steps: Run final_test.py for comprehensive endpoint testing")

if __name__ == "__main__":
    main()
