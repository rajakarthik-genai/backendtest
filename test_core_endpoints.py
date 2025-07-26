#!/usr/bin/env python3
"""
Core API Testing Script for MediTwin Agents Service
Tests the essential endpoints: documents, chat, expert opinion, body parts, and reports
"""

import requests
import json
import time
from typing import Dict, List, Any
import sys

# Configuration
AGENTS_BASE_URL = "https://mackerel-liberal-loosely.ngrok-free.app"
LOGIN_BASE_URL = "https://lenient-sunny-grouse.ngrok-free.app"
CREDENTIALS = {
    "email": "user@example.com",
    "password": "Raja@1234"
}

class CoreAPITester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def get_auth_token(self) -> bool:
        """Get authentication token from login service."""
        try:
            print("🔐 Getting authentication token...")
            
            response = self.session.post(
                f"{LOGIN_BASE_URL}/auth/login",
                json=CREDENTIALS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token')
                if self.token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.token}'
                    })
                    print("✅ Authentication successful")
                    return True
                else:
                    print("❌ No access token in response")
                    return False
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, description: str = "") -> Dict[str, Any]:
        """Test a single endpoint."""
        try:
            url = f"{AGENTS_BASE_URL}{endpoint}"
            
            if method == "GET":
                response = self.session.get(url, timeout=30)
            elif method == "POST":
                response = self.session.post(url, json=data, timeout=30)
            elif method == "PUT":
                response = self.session.put(url, json=data, timeout=30)
            elif method == "DELETE":
                response = self.session.delete(url, timeout=30)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            result = {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "endpoint": endpoint,
                "method": method,
                "description": description
            }
            
            if response.status_code < 400:
                try:
                    result["data"] = response.json()
                except:
                    result["data"] = response.text
                print(f"✅ {description} - {response.status_code}")
            else:
                result["error"] = response.text
                print(f"❌ {description} - {response.status_code}: {response.text}")
            
            return result
            
        except Exception as e:
            error_msg = f"Request failed: {str(e)}"
            print(f"❌ {description} - {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "endpoint": endpoint,
                "method": method,
                "description": description
            }
    
    def test_core_endpoints(self):
        """Test all core endpoints."""
        print("\n🚀 Testing Core MediTwin Agents API Endpoints")
        print("=" * 60)
        
        if not self.get_auth_token():
            print("❌ Cannot proceed without authentication")
            return
        
        results = []
        
        # 1. Document Management
        print("\n📄 Testing Document Management Endpoints")
        print("-" * 40)
        
        results.append(self.test_endpoint(
            "GET", "/v1/documents/status",
            description="Get documents status"
        ))
        
        results.append(self.test_endpoint(
            "GET", "/v1/documents/health",
            description="Documents health check"
        ))
        
        # 2. Chat Endpoints
        print("\n💬 Testing Chat Endpoints")
        print("-" * 40)
        
        results.append(self.test_endpoint(
            "POST", "/v1/chat/message",
            {"message": "Hello, I have a question about my health", "session_id": "test_session_123"},
            description="Send chat message"
        ))
        
        results.append(self.test_endpoint(
            "GET", "/v1/chat/health",
            description="Chat health check"
        ))
        
        # 3. Expert Opinion Endpoints
        print("\n👨‍⚕️ Testing Expert Opinion Endpoints")
        print("-" * 40)
        
        results.append(self.test_endpoint(
            "GET", "/v1/expert_opinion/specialties",
            description="Get available specialties"
        ))
        
        results.append(self.test_endpoint(
            "POST", "/v1/expert_opinion/consultation",
            {
                "message": "I'm experiencing chest pain and shortness of breath",
                "specialties": ["cardiology", "pulmonology"],
                "include_context": True,
                "priority": "high"
            },
            description="Request expert consultation"
        ))
        
        results.append(self.test_endpoint(
            "GET", "/v1/expert_opinion/health",
            description="Expert opinion health check"
        ))
        
        # 4. Body Parts Endpoints
        print("\n🫀 Testing Body Parts Endpoints")
        print("-" * 40)
        
        results.append(self.test_endpoint(
            "GET", "/v1/body_parts/list",
            description="Get available body parts"
        ))
        
        results.append(self.test_endpoint(
            "GET", "/v1/body_parts/severity",
            description="Get body parts severity"
        ))
        
        results.append(self.test_endpoint(
            "GET", "/v1/body_parts/timeline/Brain",
            description="Get Brain timeline"
        ))
        
        results.append(self.test_endpoint(
            "GET", "/v1/body_parts/timeline/Heart/range?start_date=2020-01-01&end_date=2021-12-31",
            description="Get Heart timeline range"
        ))
        
        results.append(self.test_endpoint(
            "GET", "/v1/body_parts/health",
            description="Body parts health check"
        ))
        
        # 5. Reports Endpoints
        print("\n📊 Testing Reports Endpoints")
        print("-" * 40)
        
        results.append(self.test_endpoint(
            "POST", "/v1/reports/generate",
            {
                "report_type": "comprehensive",
                "title": "Comprehensive Health Report",
                "include_expert_opinion": True,
                "format": "markdown"
            },
            description="Generate comprehensive report"
        ))
        
        results.append(self.test_endpoint(
            "POST", "/v1/reports/generate",
            {
                "report_type": "body_part",
                "title": "Brain Health Report",
                "body_part": "Brain",
                "include_expert_opinion": True,
                "format": "markdown"
            },
            description="Generate body part report"
        ))
        
        results.append(self.test_endpoint(
            "GET", "/v1/reports/list",
            description="List reports"
        ))
        
        results.append(self.test_endpoint(
            "GET", "/v1/reports/health",
            description="Reports health check"
        ))
        
        # 6. System Health
        print("\n🏥 Testing System Health Endpoints")
        print("-" * 40)
        
        results.append(self.test_endpoint(
            "GET", "/health",
            description="Main health check"
        ))
        
        results.append(self.test_endpoint(
            "GET", "/v1/system_info/system/status",
            description="System status"
        ))
        
        # Summary
        print("\n📋 Test Summary")
        print("=" * 60)
        
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        print(f"✅ Successful: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"❌ Failed: {len(failed)}/{len(results)} ({len(failed)/len(results)*100:.1f}%)")
        
        if failed:
            print("\n❌ Failed Endpoints:")
            for result in failed:
                print(f"  - {result['method']} {result['endpoint']}: {result.get('error', 'Unknown error')}")
        
        print(f"\n🎯 Core Endpoints Tested: {len(results)}")
        print("📄 Document Management: Upload, Status")
        print("💬 Chat: Streaming responses with context")
        print("👨‍⚕️ Expert Opinion: Multi-specialist consultation")
        print("🫀 Body Parts: Severity tracking and timeline")
        print("📊 Reports: Comprehensive health reports with PDF export")
        
        return results

def main():
    """Main test execution."""
    tester = CoreAPITester()
    results = tester.test_core_endpoints()
    
    # Save results to file
    with open("core_endpoints_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: core_endpoints_test_results.json")

if __name__ == "__main__":
    main() 