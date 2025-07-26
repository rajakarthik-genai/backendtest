#!/usr/bin/env python3
"""
Quick token getter for MediTwin authentication
"""

import requests
import json
import sys

# Configuration
LOGIN_SERVICE_URL = "https://lenient-sunny-grouse.ngrok-free.app"
LOGIN_CREDENTIALS = {
    "email": "user@example.com",
    "password": "Raja@1234"
}

def get_token():
    """Get authentication token from login service"""
    print("🔐 Getting authentication token...")
    
    # Try common login endpoints
    login_endpoints = [
        f"{LOGIN_SERVICE_URL}/api/v1/auth/login",
        f"{LOGIN_SERVICE_URL}/auth/login",
        f"{LOGIN_SERVICE_URL}/login", 
        f"{LOGIN_SERVICE_URL}/api/login",
        f"{LOGIN_SERVICE_URL}/api/v1/login"
    ]
    
    session = requests.Session()
    session.timeout = 30
    
    for endpoint in login_endpoints:
        try:
            print(f"  Trying: {endpoint}")
            response = session.post(
                endpoint,
                json=LOGIN_CREDENTIALS,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"  Response: {json.dumps(data, indent=2)}")
                
                # Try different token field names
                token_fields = ["access_token", "token", "authToken", "jwt", "accessToken"]
                
                for field in token_fields:
                    if field in data:
                        token = data[field]
                        print(f"✅ Found token in field '{field}': {token[:50]}...")
                        return token
                        
                print("❌ No token found in response")
                return None
                
            else:
                print(f"  Error: {response.text}")
                
        except Exception as e:
            print(f"  Exception: {e}")
            continue
    
    print("❌ Could not get token from any endpoint")
    return None

if __name__ == "__main__":
    token = get_token()
    if token:
        print(f"\n🎉 Success! Token: {token}")
        
        # Test the token with a simple request
        print("\n🧪 Testing token with agents service...")
        try:
            response = requests.get(
                "https://mackerel-liberal-loosely.ngrok-free.app/health",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            print(f"Health check status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Token works!")
            else:
                print(f"⚠️  Health check returned: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing token: {e}")
    else:
        print("❌ Failed to get token")
        sys.exit(1)
