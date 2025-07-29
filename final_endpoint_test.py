#!/usr/bin/env python3
"""
Final comprehensive endpoint testing for Medical Digital Twin API
"""

import requests
import json
import time

def comprehensive_endpoint_test():
    """Comprehensive endpoint testing with JWT authentication"""
    print("🚀 FINAL COMPREHENSIVE ENDPOINT TESTING")
    print("=" * 60)
    
    # Configuration
    login_url = "https://lenient-sunny-grouse.ngrok-free.app"
    agents_url = "https://mackerel-liberal-loosely.ngrok-free.app"
    
    # Step 1: Get fresh JWT token
    print("\n1️⃣ Getting JWT token...")
    try:
        login_response = requests.post(
            f"{login_url}/auth/login",
            json={"email": "user@example.com", "password": "Raja@1234"},
            timeout=10
        )
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data["access_token"]
            print(f"✅ Token obtained successfully")
            
            # Verify token
            import jwt
            decoded = jwt.decode(token, options={"verify_signature": False})
            print(f"📋 Token payload: {decoded}")
            
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting token: {e}")
        return False
    
    # Step 2: Test service health
    print("\n2️⃣ Testing service health...")
    try:
        health_response = requests.get(f"{agents_url}/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print("✅ Service health:")
            print(json.dumps(health_data, indent=2))
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Step 3: Comprehensive endpoint testing
    print("\n3️⃣ Testing all endpoints...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test cases organized by category
    test_cases = {
        "Health": [
            ("GET", f"{agents_url}/health"),
            ("GET", f"{agents_url}/api/v1/health/body-parts"),
            ("GET", f"{agents_url}/api/v1/health/summary"),
            ("GET", f"{agents_url}/api/v1/health/status"),
        ],
        
        "Documents": [
            ("GET", f"{agents_url}/api/v1/documents/status"),
            ("GET", f"{agents_url}/api/v1/documents"),
            ("POST", f"{agents_url}/api/v1/documents/upload"),
        ],
        
        "Timeline": [
            ("GET", f"{agents_url}/api/v1/timeline/events"),
            ("GET", f"{agents_url}/api/v1/timeline/summary"),
            ("GET", f"{agents_url}/api/v1/timeline"),
        ],
        
        "Chat": [
            ("POST", f"{agents_url}/api/v1/chat/message", {"query": "Hello, how are you feeling today?"}),
            ("GET", f"{agents_url}/api/v1/chat/history"),
        ],
        
        "Reports": [
            ("GET", f"{agents_url}/api/v1/reports"),
            ("GET", f"{agents_url}/api/v1/reports/list"),
            ("POST", f"{agents_url}/api/v1/reports/generate"),
        ],
        
        "Expert Opinion": [
            ("POST", f"{agents_url}/api/v1/expert-opinion", {"query": "What are the symptoms of flu?"}),
            ("GET", f"{agents_url}/api/v1/expert-opinion"),
        ],
        
        "3D Visualization": [
            ("GET", f"{agents_url}/api/v1/3d/model"),
            ("GET", f"{agents_url}/api/v1/3d/heatmap"),
        ]
    }
    
    results = {}
    total_tests = 0
    successful_tests = 0
    
    for category, endpoints in test_cases.items():
        print(f"\n📂 {category} Endpoints:")
        category_results = []
        
        for test_case in endpoints:
            method, url = test_case[0], test_case[1]
            data = test_case[2] if len(test_case) > 2 else None
            
            try:
                if method == "GET":
                    response = requests.get(url, headers=headers, timeout=15)
                else:
                    response = requests.post(url, headers=headers, json=data, timeout=15)
                
                result = {
                    "status": response.status_code,
                    "success": response.status_code == 200,
                    "response": response.text[:200] if response.status_code != 200 else "OK"
                }
                
                category_results.append(result)
                total_tests += 1
                
                if response.status_code == 200:
                    successful_tests += 1
                    print(f"  ✅ {method} {url}: 200 OK")
                else:
                    print(f"  ❌ {method} {url}: {response.status_code}")
                    
            except Exception as e:
                result = {
                    "status": "ERROR",
                    "success": False,
                    "response": str(e)
                }
                category_results.append(result)
                total_tests += 1
                print(f"  ❌ {method} {url}: ERROR - {e}")
        
        results[category] = category_results
    
    # Step 4: Generate comprehensive report
    print(f"\n📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    # Categorize failures
    auth_failures = []
    server_errors = []
    method_errors = []
    other_errors = []
    
    for category, category_results in results.items():
        for result in category_results:
            if not result["success"]:
                if result["status"] == 401:
                    auth_failures.append(f"{category}: 401 Unauthorized")
                elif str(result["status"]).startswith("5"):
                    server_errors.append(f"{category}: {result['status']} Server Error")
                elif result["status"] == 405:
                    method_errors.append(f"{category}: 405 Method Not Allowed")
                else:
                    other_errors.append(f"{category}: {result['status']} {result['response']}")
    
    if auth_failures:
        print(f"\n❌ Authentication Issues (401): {len(auth_failures)}")
        for failure in auth_failures:
            print(f"   - {failure}")
    
    if server_errors:
        print(f"\n❌ Server Errors (5xx): {len(server_errors)}")
        for error in server_errors:
            print(f"   - {error}")
    
    if method_errors:
        print(f"\n❌ Method Issues (405): {len(method_errors)}")
        for error in method_errors:
            print(f"   - {error}")
    
    if other_errors:
        print(f"\n❌ Other Issues: {len(other_errors)}")
        for error in other_errors:
            print(f"   - {error}")
    
    # Save detailed results
    with open('final_test_results.json', 'w') as f:
        json.dump({
            "timestamp": time.time(),
            "summary": {
                "total_tests": total_tests,
                "successful": successful_tests,
                "failed": total_tests - successful_tests,
                "success_rate": (successful_tests/total_tests)*100
            },
            "results": results,
            "token_used": token[:50] + "..."
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to final_test_results.json")
    
    # Final status
    if successful_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! JWT authentication is working correctly.")
        return True
    elif successful_tests > 0:
        print(f"\n⚠️ PARTIAL SUCCESS: {successful_tests}/{total_tests} tests passed.")
        return False
    else:
        print("\n❌ ALL TESTS FAILED. JWT authentication needs further debugging.")
        return False

def main():
    """Main testing function"""
    success = comprehensive_endpoint_test()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Medical Digital Twin API testing completed successfully!")
    else:
        print("⚠️ Some issues remain. Check final_test_results.json for details.")
    
    print("\n🔍 Next Steps:")
    print("1. Review final_test_results.json for detailed analysis")
    print("2. Check JWT middleware configuration if 401 errors persist")
    print("3. Verify database connectivity for 5xx errors")
    print("4. Check endpoint documentation for correct HTTP methods")

if __name__ == "__main__":
    main()
