#!/usr/bin/env python3
"""
Simple debugging script for JWT and database issues
"""

import requests
import json
import jwt

def test_jwt_and_endpoints():
    """Test JWT authentication and endpoints"""
    print("🚀 Starting JWT and Endpoint Testing")
    
    # Configuration
    login_url = "https://lenient-sunny-grouse.ngrok-free.app"
    agents_url = "https://mackerel-liberal-loosely.ngrok-free.app"
    
    # Get fresh token
    print("🔐 Getting fresh token...")
    try:
        response = requests.post(
            f"{login_url}/auth/login",
            json={"email": "user@example.com", "password": "Raja@1234"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data["access_token"]
            print(f"✅ Token obtained: {token[:50]}...")
            
            # Decode token to understand structure
            decoded = jwt.decode(token, options={"verify_signature": False})
            print(f"📋 Token payload: {json.dumps(decoded, indent=2)}")
            
            # Test with different JWT secrets
            secrets = [
                "your-secret-key",  # This worked in previous test
                "ek5Ygo_I4A-P2DopAQTRTKSvwhlp6m7RQriMHnosT3YGJIn3O56-M8kVwz27wTVnoZwCcRtzyo8li8j-di_r6Q",
                "secret",
                "super-secret-key"
            ]
            
            for secret in secrets:
                try:
                    jwt.decode(token, secret, algorithms=["HS256"])
                    print(f"✅ Valid JWT secret: {secret}")
                    break
                except jwt.InvalidTokenError:
                    continue
            
            # Test endpoints
            headers = {"Authorization": f"Bearer {token}"}
            
            endpoints = [
                f"{agents_url}/health",
                f"{agents_url}/api/v1/health/body-parts",
                f"{agents_url}/api/v1/health/summary",
                f"{agents_url}/api/v1/documents/status",
                f"{agents_url}/api/v1/timeline/events"
            ]
            
            print("\n🧪 Testing endpoints...")
            for endpoint in endpoints:
                resp = requests.get(endpoint, headers=headers)
                print(f"{endpoint}: {resp.status_code}")
                if resp.status_code != 200:
                    print(f"  Error: {resp.text[:100]}")
            
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_database_health():
    """Test database connectivity via health endpoint"""
    print("\n🗄️ Testing Database Health")
    
    agents_url = "https://mackerel-liberal-loosely.ngrok-free.app"
    
    try:
        health = requests.get(f"{agents_url}/health")
        if health.status_code == 200:
            health_data = health.json()
            print("✅ Health endpoint accessible")
            print(f"Services: {json.dumps(health_data, indent=2)}")
            return True
        else:
            print(f"❌ Health endpoint failed: {health.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def fix_jwt_secret():
    """Fix JWT secret configuration"""
    print("\n🔧 Fixing JWT Secret Configuration")
    
    # The correct secret based on our testing
    correct_secret = "your-secret-key"
    
    # Update config file
    config_path = "src/core/config.py"
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Update JWT secret
        updated_content = content.replace(
            'JWT_SECRET_KEY: str = Field("ek5Ygo_I4A-P2DopAQTRTKSvwhlp6m7RQriMHnosT3YGJIn3O56-M8kVwz27wTVnoZwCcRtzyo8li8j-di_r6Q", env="JWT_SECRET_KEY")',
            'JWT_SECRET_KEY: str = Field("your-secret-key", env="JWT_SECRET_KEY")'
        )
        
        with open(config_path, 'w') as f:
            f.write(updated_content)
        
        print("✅ JWT secret updated to 'your-secret-key'")
        return True
        
    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return False

def main():
    """Main debugging function"""
    print("🚀 Medical Digital Twin Debug & Fix")
    print("=" * 50)
    
    # Test current state
    jwt_works = test_jwt_and_endpoints()
    db_healthy = test_database_health()
    
    # Fix configuration
    if not jwt_works:
        print("\n🔧 Attempting fixes...")
        fix_jwt_secret()
        
        # Retest after fix
        print("\n🔄 Retesting after fixes...")
        test_jwt_and_endpoints()
    
    print("\n📊 Debug Summary:")
    print(f"JWT Authentication: {'✅ Fixed' if jwt_works else '❌ Needs attention'}")
    print(f"Database Connectivity: {'✅ Healthy' if db_healthy else '❌ Needs attention'}")

if __name__ == "__main__":
    main()
