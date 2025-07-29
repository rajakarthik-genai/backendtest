#!/usr/bin/env python3
"""
JWT Fix Script
"""

import requests
import json
import os
from pathlib import Path

def fix_jwt_configuration():
    """Fix JWT configuration across services"""
    
    # Configuration
    jwt_secret = "your-secret-key"
    
    # Update configuration files
    config_files = [
        "src/core/config.py",
        ".env"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"📝 Updating {config_file}...")
            
            with open(config_file, 'r') as f:
                content = f.read()
            
            # Update JWT secret
            updated = False
            if 'JWT_SECRET_KEY' in content:
                lines = content.split('\n')
                updated_lines = []
                for line in lines:
                    if 'JWT_SECRET_KEY' in line and 'your-secret-key' not in line:
                        updated_lines.append(f'JWT_SECRET_KEY="your-secret-key"')
                        updated = True
                    else:
                        updated_lines.append(line)
                
                if updated:
                    with open(config_file, 'w') as f:
                        f.write('\n'.join(updated_lines))
                    print(f"✅ Updated {config_file}")
                else:
                    print(f"ℹ️ {config_file} already has correct JWT secret")

def test_after_fix():
    """Test endpoints after fix"""
    login_url = "https://lenient-sunny-grouse.ngrok-free.app"
    agents_url = "https://mackerel-liberal-loosely.ngrok-free.app"
    
    # Get token
    response = requests.post(
        f"{login_url}/auth/login",
        json={"email": "user@example.com", "password": "Raja@1234"}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test basic endpoint
        test_response = requests.get(
            f"{agents_url}/api/v1/health/body-parts",
            headers=headers
        )
        
        print(f"Test result: {test_response.status_code}")
        if test_response.status_code == 200:
            print("✅ JWT authentication working!")
        else:
            print(f"❌ Still failing: {test_response.text}")

if __name__ == "__main__":
    fix_jwt_configuration()
    test_after_fix()
