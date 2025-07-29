#!/usr/bin/env python3
"""
Comprehensive debugging and fixing script for JWT and database issues
"""

import jwt
import requests
import json
import os
import sys
from pathlib import Path

# Add the src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.config import settings
from db.mongodb import get_database
from db.neo4j import neo4j_connection
from db.redis_db import get_redis

def test_jwt_configuration():
    """Test JWT configuration and token validation"""
    print("🔍 Testing JWT Configuration")
    print(f"Current JWT_SECRET_KEY: {settings.JWT_SECRET_KEY[:20]}...")
    
    # Get a fresh token
    login_url = "https://lenient-sunny-grouse.ngrok-free.app"
    agents_url = "https://mackerel-liberal-loosely.ngrok-free.app"
    
    try:
        response = requests.post(
            f"{login_url}/auth/login",
            json={"email": "user@example.com", "password": "Raja@1234"}
        )
        token = response.json()["access_token"]
        
        # Decode token without verification
        decoded = jwt.decode(token, options={"verify_signature": False})
        print(f"Token decoded: {decoded}")
        
        # Test with current secret
        try:
            jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
            print("✅ Token valid with current secret")
            return True
        except jwt.InvalidTokenError as e:
            print(f"❌ Token invalid with current secret: {e}")
            
            # Try to determine the correct secret
            print("🔍 Determining correct JWT secret...")
            
            # Test common secrets
            common_secrets = [
                "your-secret-key",
                "secret",
                "super-secret-key",
                "jwt-secret-key",
                "medical-twin-secret",
                "development-secret-key"
            ]
            
            for secret in common_secrets:
                try:
                    jwt.decode(token, secret, algorithms=["HS256"])
                    print(f"✅ Token valid with secret: {secret}")
                    
                    # Update the configuration
                    print(f"📝 Updating JWT_SECRET_KEY to: {secret}")
                    
                    # Update config file
                    config_path = Path(__file__).parent / 'src' / 'core' / 'config.py'
                    with open(config_path, 'r') as f:
                        content = f.read()
                    
                    updated_content = content.replace(
                        f'JWT_SECRET_KEY: str = Field("{settings.JWT_SECRET_KEY}", env="JWT_SECRET_KEY")',
                        f'JWT_SECRET_KEY: str = Field("{secret}", env="JWT_SECRET_KEY")'
                    )
                    
                    with open(config_path, 'w') as f:
                        f.write(updated_content)
                    
                    print("✅ JWT secret updated successfully")
                    return secret
                    
                except jwt.InvalidTokenError:
                    continue
            
            print("❌ Could not determine correct JWT secret")
            return False
            
    except Exception as e:
        print(f"❌ Error testing JWT: {e}")
        return False

def test_database_connections():
    """Test database connectivity"""
    print("\n🗄️ Testing Database Connections")
    
    try:
        # Test MongoDB
        print("Testing MongoDB...")
        mongo = get_database()
        mongo.admin.command('ping')
        print("✅ MongoDB connected")
        
        # Test Neo4j
        print("Testing Neo4j...")
        neo4j = neo4j_connection
        neo4j.verify_connectivity()
        print("✅ Neo4j connected")
        
        # Test Redis
        print("Testing Redis...")
        redis = get_redis()
        redis.ping()
        print("✅ Redis connected")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def test_endpoints_after_fix():
    """Test endpoints after fixes"""
    print("\n🧪 Testing Endpoints After Fixes")
    
    # Get fresh token
    login_url = "https://lenient-sunny-grouse.ngrok-free.app"
    agents_url = "https://mackerel-liberal-loosely.ngrok-free.app"
    
    try:
        response = requests.post(
            f"{login_url}/auth/login",
            json={"email": "user@example.com", "password": "Raja@1234"}
        )
        token = response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test endpoints
        tests = [
            ("GET", f"{agents_url}/api/v1/health/body-parts"),
            ("GET", f"{agents_url}/api/v1/health/summary"),
            ("GET", f"{agents_url}/api/v1/documents/status"),
            ("POST", f"{agents_url}/api/v1/chat/message", {"query": "test"}),
        ]
        
        results = []
        for method, url, *data in tests:
            if method == "GET":
                resp = requests.get(url, headers=headers)
            else:
                resp = requests.post(url, headers=headers, json=data[0])
            
            results.append((url, resp.status_code, resp.text[:100]))
            print(f"{method} {url}: {resp.status_code}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")
        return []

def main():
    """Main debugging function"""
    print("🚀 Starting Comprehensive Debug & Fix")
    
    # Test JWT configuration
    jwt_fixed = test_jwt_configuration()
    
    # Test database connections
    db_connected = test_database_connections()
    
    # Test endpoints
    results = test_endpoints_after_fix()
    
    print("\n📊 Debug Results Summary:")
    print(f"JWT Fixed: {'✅' if jwt_fixed else '❌'}")
    print(f"DB Connected: {'✅' if db_connected else '❌'}")
    print(f"Endpoints Tested: {len(results)}")
    
    for url, status, response in results:
        print(f"  {url}: {status}")

if __name__ == "__main__":
    main()
