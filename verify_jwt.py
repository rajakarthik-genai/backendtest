#!/usr/bin/env python3
"""
JWT verification and endpoint testing
"""

import requests
import json
import jwt

def test_jwt_validation():
    """Test JWT token validation directly"""
    print("🔍 Testing JWT Token Validation")
    
    # Get fresh token
    login_url = "https://lenient-sunny-grouse.ngrok-free.app"
    agents_url = "https://mackerel-liberal-loosely.ngrok-free.app"
    
    # Login and get token
    response = requests.post(
        f"{login_url}/auth/login",
        json={"email": "user@example.com", "password": "Raja@1234"}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Token obtained: {token[:50]}...")
        
        # Test token decoding with different secrets
        secrets = [
            "your-secret-key",
            "secret",
            "super-secret-key"
        ]
        
        for secret in secrets:
            try:
                decoded = jwt.decode(token, secret, algorithms=["HS256"])
                print(f"✅ Valid with secret: {secret}")
                print(f"📋 Token payload: {json.dumps(decoded, indent=2)}")
                
                # Test endpoints with this token
                headers = {"Authorization": f"Bearer {token}"}
                
                print("\n🧪 Testing endpoints...")
                endpoints = [
                    f"{agents_url}/api/v1/health/body-parts",
                    f"{agents_url}/api/v1/health/summary",
                    f"{agents_url}/api/v1/documents/status"
                ]
                
                for endpoint in endpoints:
                    resp = requests.get(endpoint, headers=headers)
                    print(f"  {endpoint}: {resp.status_code}")
                    if resp.status_code == 200:
                        print(f"    ✅ Success")
                    else:
                        print(f"    ❌ {resp.text[:100]}")
                
                return secret
                
            except jwt.InvalidTokenError:
                continue
    
    return None

def test_database_connectivity():
    """Test database connectivity"""
    print("\n🗄️ Testing Database Connectivity")
    
    agents_url = "https://mackerel-liberal-loosely.ngrok-free.app"
    
    try:
        # Test health endpoint
        health = requests.get(f"{agents_url}/health")
        if health.status_code == 200:
            health_data = health.json()
            print("✅ Health endpoint accessible")
            
            services = health_data.get('services', {})
            for service, status in services.items():
                print(f"  {service}: {'✅' if status else '❌'}")
            
            return True
        else:
            print(f"❌ Health endpoint failed: {health.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def main():
    """Main testing function"""
    print("🚀 Medical Digital Twin JWT & Database Testing")
    print("=" * 50)
    
    # Test JWT and endpoints
    valid_secret = test_jwt_validation()
    if valid_secret:
        print(f"\n✅ JWT validation successful with secret: {valid_secret}")
    else:
        print("\n❌ JWT validation failed")
    
    # Test database connectivity
    db_healthy = test_database_connectivity()
    
    print("\n📊 Final Results:")
    print(f"JWT Secret: {'✅ Valid' if valid_secret else '❌ Invalid'}")
    print(f"Database: {'✅ Connected' if db_healthy else '❌ Issues'}")

if __name__ == "__main__":
    main()
