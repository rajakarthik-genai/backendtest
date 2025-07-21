#!/usr/bin/env python3
"""
Quick test to verify ChatResponse fixes
"""
import requests
import sys

def test_endpoint(endpoint, method="GET", data=None):
    url = f"http://localhost:8000/api/v1{endpoint}"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyX1BUX0E1RjRGQkM2N0Q3NDRFRjI4MjM4OUFEMEY3NjMzQTQiLCJwYXRpZW50X2lkIjoiUFRfQTVGNEZCQzY3RDc0NEVGMjgyMzg5QUQwRjc2MzNBNCIsImV4cCI6MTc1MzQzNDQ5Nn0.h6-lGllc7kWiAGLt5V_5EO6kj0B6G6RK8SjuPKJiKb4",
        "Content-Type": "application/json"
    }
    
    try:
        if method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            response = requests.get(url, headers=headers, timeout=10)
        
        print(f"✅ {endpoint} - Status: {response.status_code}")
        if response.status_code == 200:
            return True
        else:
            print(f"   Error: {response.text[:100]}...")
            return False
    except Exception as e:
        print(f"❌ {endpoint} - Error: {e}")
        return False

def main():
    print("🔧 Testing Fixed Endpoints")
    print("=" * 40)
    
    tests = [
        ("/medical_analysis/symptoms/analyze", "POST", {
            "symptoms": ["headache"], 
            "duration": "1 day", 
            "severity": "mild"
        }),
        ("/knowledge_base/knowledge/search?query=diabetes", "GET", None),
        ("/system_info/system/status", "GET", None),
    ]
    
    passed = 0
    total = len(tests)
    
    for endpoint, method, data in tests:
        if test_endpoint(endpoint, method, data):
            passed += 1
    
    print("=" * 40)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All ChatResponse fixes are working!")
    else:
        print("⚠️  Some endpoints still have issues")

if __name__ == "__main__":
    main()
