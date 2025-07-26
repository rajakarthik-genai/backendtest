#!/usr/bin/env python3
"""
Comprehensive test suite for MediTwin Agents API with authentication.
This script:
1. Gets an authentication token from the login service
2. Tests all available endpoints in the agents service
3. Provides detailed results and statistics
"""

import requests
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os

# Configuration
LOGIN_SERVICE_URL = "https://lenient-sunny-grouse.ngrok-free.app"
AGENTS_SERVICE_URL = "https://mackerel-liberal-loosely.ngrok-free.app"
LOGIN_CREDENTIALS = {
    "email": "user@example.com",
    "password": "Raja@1234"
}

class Color:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class MediTwinTester:
    """Comprehensive tester for MediTwin Agents API"""
    
    def __init__(self):
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        self.test_results = []
        self.session = requests.Session()
        self.session.timeout = 30
        
    def print_status(self, message: str, status: str = "INFO"):
        """Print colored status messages"""
        colors = {
            "INFO": Color.BLUE,
            "SUCCESS": Color.GREEN,
            "ERROR": Color.RED,
            "WARNING": Color.YELLOW,
            "TITLE": Color.PURPLE + Color.BOLD
        }
        color = colors.get(status, Color.WHITE)
        print(f"{color}{message}{Color.END}")
        
    def get_ngrok_url(self) -> Optional[str]:
        """Get the ngrok URL for the login service"""
        self.print_status("🔍 Looking for ngrok tunnels...", "INFO")
        
        try:
            # Try to get ngrok tunnels
            response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get("tunnels", [])
                
                for tunnel in tunnels:
                    if "backend" in tunnel.get("name", "").lower():
                        url = tunnel["public_url"]
                        self.print_status(f"✅ Found ngrok URL: {url}", "SUCCESS")
                        return url
                        
                # If no backend tunnel found, use the first HTTPS tunnel
                for tunnel in tunnels:
                    if tunnel["proto"] == "https":
                        url = tunnel["public_url"]
                        self.print_status(f"✅ Using ngrok URL: {url}", "SUCCESS")
                        return url
                        
        except Exception as e:
            self.print_status(f"❌ Could not get ngrok URL: {e}", "ERROR")
            
        # Fallback - ask user for URL
        url = input("🔗 Please enter the ngrok URL for the login service: ").strip()
        return url if url else None
        
    def get_auth_token(self) -> bool:
        """Get authentication token from login service"""
        self.print_status("🔐 Attempting to get authentication token...", "INFO")
        
        try:
            # Try common login endpoints for the known login service
            login_endpoints = [
                f"{LOGIN_SERVICE_URL}/api/v1/auth/login",
                f"{LOGIN_SERVICE_URL}/auth/login", 
                f"{LOGIN_SERVICE_URL}/login",
                f"{LOGIN_SERVICE_URL}/api/login"
            ]
            
            for endpoint in login_endpoints:
                try:
                    self.print_status(f"  Trying: {endpoint}", "INFO")
                    response = self.session.post(
                        endpoint, 
                        json=LOGIN_CREDENTIALS,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        # Try different token field names
                        token_fields = ["access_token", "token", "authToken", "jwt", "accessToken"]
                        
                        for field in token_fields:
                            if field in data:
                                self.token = data[field]
                                break
                                
                        if self.token:
                            self.headers["Authorization"] = f"Bearer {self.token}"
                            self.print_status("✅ Successfully obtained authentication token", "SUCCESS")
                            return True
                            
                except Exception as e:
                    self.print_status(f"  Failed: {e}", "WARNING")
                    continue
                    
            self.print_status("❌ Could not get authentication token from any endpoint", "ERROR")
            return False
            
        except Exception as e:
            self.print_status(f"❌ Authentication failed: {e}", "ERROR")
            return False
            
    def test_endpoint(self, method: str, url: str, payload: Optional[Dict] = None, 
                     files: Optional[Dict] = None, description: str = "") -> Dict[str, Any]:
        """Test a single endpoint and record results"""
        
        start_time = time.time()
        result = {
            "endpoint": url,
            "method": method,
            "description": description,
            "status_code": None,
            "response_time": None,
            "success": False,
            "error": None,
            "response_data": None
        }
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=self.headers)
            elif method.upper() == "POST":
                if files:
                    # For file uploads, don't send Content-Type header
                    upload_headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
                    response = self.session.post(url, files=files, headers=upload_headers)
                else:
                    response = self.session.post(url, json=payload, headers=self.headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=payload, headers=self.headers)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            result["status_code"] = response.status_code
            result["response_time"] = round(time.time() - start_time, 3)
            
            # Consider successful if status is 200-299 or certain expected codes
            if response.status_code in range(200, 300) or response.status_code in [401, 422]:
                result["success"] = True
                try:
                    result["response_data"] = response.json()
                except:
                    result["response_data"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
            else:
                result["error"] = f"HTTP {response.status_code}: {response.text[:100]}"
                
        except Exception as e:
            result["error"] = str(e)
            result["response_time"] = round(time.time() - start_time, 3)
            
        self.test_results.append(result)
        return result
        
    def run_all_tests(self) -> None:
        """Run comprehensive tests on all endpoints"""
        
        base_url = f"{AGENTS_SERVICE_URL}/v1"
        
        self.print_status("🧪 Starting comprehensive API testing...", "TITLE")
        self.print_status("=" * 60, "INFO")
        
        # Test categories with their endpoints
        test_suites = {
            "Health & System": [
                ("GET", f"{AGENTS_SERVICE_URL}/health", None, "Basic health check"),
                ("GET", f"{base_url}/system_info/system/status", None, "System status"),
                ("GET", f"{base_url}/system_info/info", None, "System information"),
                ("GET", f"{base_url}/system_info/metrics", None, "System metrics"),
                ("GET", f"{base_url}/system_info/database/status", None, "Database status"),
            ],
            
            "Chat & Messaging": [
                ("POST", f"{base_url}/chat/message", {
                    "message": "I have a headache and feel tired",
                    "session_id": "test-session-123"
                }, "Send chat message"),
                ("GET", f"{base_url}/chat/history/test-session-123", None, "Get chat history"),
                ("GET", f"{base_url}/chat/sessions", None, "Get chat sessions"), 
                ("DELETE", f"{base_url}/chat/history/test-session-123", None, "Clear chat history"),
                ("POST", f"{base_url}/chat/chat", {
                    "message": "Hello, I need medical advice"
                }, "Basic chat"),
            ],
            
            "Medical Analysis": [
                ("POST", f"{base_url}/medical_analysis/symptoms/analyze", {
                    "symptoms": ["headache", "fever", "fatigue"],
                    "duration": "3 days",
                    "severity": "moderate",
                    "context": "Started after stress at work"
                }, "Analyze symptoms"),
                ("POST", f"{base_url}/medical_analysis/diagnostic/suggestions", {
                    "symptoms": ["cough", "shortness of breath"],
                    "medical_history": "Previous respiratory issues",
                    "age": 35,
                    "gender": "male"
                }, "Get diagnostic suggestions"),
                ("POST", f"{base_url}/medical_analysis/treatment/recommendations", {
                    "condition": "common cold",
                    "symptoms": ["runny nose", "cough"],
                    "severity": "mild",
                    "allergies": []
                }, "Get treatment recommendations"),
            ],
            
            "Knowledge Base": [
                ("GET", f"{base_url}/knowledge_base/knowledge/search?query=diabetes", None, "Search knowledge base"),
                ("GET", f"{base_url}/knowledge_base/medical/information?topic=hypertension", None, "Get medical information"),
                ("POST", f"{base_url}/knowledge_base/drugs/interactions", {
                    "medications": ["aspirin", "ibuprofen", "lisinopril"]
                }, "Check drug interactions"),
            ],
            
            "Analytics & Health Metrics": [
                ("GET", f"{base_url}/analytics/analytics/trends?period=30d", None, "Get analytics trends"),
                ("GET", f"{base_url}/analytics/analytics/dashboard", None, "Get analytics dashboard"),
                ("GET", f"{base_url}/analytics/health/score", None, "Get health score"),
                ("GET", f"{base_url}/analytics/health/risk-assessment", None, "Get risk assessment"),
            ],
            
            "Timeline & Events": [
                ("GET", f"{base_url}/timeline/timeline", None, "Get timeline events"),
                ("GET", f"{base_url}/timeline/summary", None, "Get timeline summary"),
                ("POST", f"{base_url}/timeline/timeline", {
                    "event_type": "symptom",
                    "description": "Experienced headache",
                    "timestamp": datetime.now().isoformat(),
                    "severity": "moderate"
                }, "Create timeline event"),
                ("GET", f"{base_url}/timeline/timeline/statistics", None, "Get timeline statistics"),
            ],
            
            "Document Upload": [
                ("GET", f"{base_url}/upload/documents", None, "List uploaded documents"),
                ("GET", f"{base_url}/upload/status/test-doc-123", None, "Get upload status"),
                ("GET", f"{base_url}/documents/documents", None, "Get documents"),
                ("GET", f"{base_url}/documents/list", None, "List documents"),
                ("GET", f"{base_url}/documents/health", None, "Documents health check"),
            ],
            
            "User Profile": [
                ("GET", f"{base_url}/user_profile/user/profile", None, "Get user profile"),
                ("PUT", f"{base_url}/user_profile/user/profile", {
                    "name": "Test User",
                    "age": 30,
                    "gender": "male",
                    "medical_conditions": ["hypertension"]
                }, "Update user profile"),
                ("GET", f"{base_url}/user_profile/user/preferences", None, "Get user preferences"),
                ("GET", f"{base_url}/user_profile/user/settings", None, "Get user settings"),
            ],
            
            "Expert Opinion": [
                ("POST", f"{base_url}/expert_opinion/expert-opinion", {
                    "specialty": "cardiology",
                    "case_description": "Patient with chest pain and shortness of breath",
                    "symptoms": ["chest pain", "shortness of breath"],
                    "urgency": "medium"
                }, "Request expert opinion"),
                ("GET", f"{base_url}/expert_opinion/expert-opinion", None, "Get expert opinion requests"),
                ("GET", f"{base_url}/expert_opinion/specialties", None, "Get available specialties"),
                ("GET", f"{base_url}/expert_opinion/expert-opinion/status", None, "Get expert opinion status"),
            ],
            
            "Tools & Utilities": [
                ("GET", f"{base_url}/tools/", None, "Get available tools"),
                ("POST", f"{base_url}/tools/get_timeline", {
                    "parameters": {"period": "30d"}
                }, "Get timeline tool"),
                ("POST", f"{base_url}/tools/get_body_part_status", {
                    "parameters": {"body_part": "head"}
                }, "Get body part status tool"),
                ("POST", f"{base_url}/tools/search_medical_records", {
                    "parameters": {"query": "headache"}
                }, "Search medical records tool"),
            ],
            
            "Anatomy": [
                ("GET", f"{base_url}/anatomy/body-parts", None, "Get body parts"),
                ("GET", f"{base_url}/anatomy/regions", None, "Get body regions"),
                ("GET", f"{base_url}/anatomy/config/body-parts", None, "Get configured body parts"),
                ("GET", f"{base_url}/anatomy/", None, "Anatomy overview"),
            ],
            
            "Events": [
                ("GET", f"{base_url}/events/", None, "Get events"),
                ("POST", f"{base_url}/events/", {
                    "event_type": "symptom",
                    "description": "Test event from API testing",
                    "severity": "mild"
                }, "Create event"),
            ],
            
            "Export": [
                ("GET", f"{base_url}/export/health/export", None, "Export health report"),
                ("GET", f"{base_url}/export/timeline/export", None, "Export timeline"),
            ],
            
            "OpenAI Compatible": [
                ("POST", f"{base_url}/openai_compatible/v1/chat/completions", {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "What are symptoms of flu?"}],
                    "max_tokens": 100
                }, "OpenAI compatible chat"),
                ("GET", f"{base_url}/openai_compatible/v1/models", None, "List available models"),
                ("GET", f"{base_url}/openai_compatible/v1/health", None, "OpenAI API health check"),
            ],
            
            "Admin": [
                ("GET", f"{base_url}/admin/users", None, "Get users (admin)"),
                ("GET", f"{base_url}/admin/system/health", None, "System health (admin)"),
                ("GET", f"{base_url}/admin/logs", None, "Get system logs (admin)"),
            ]
        }
        
        # Run tests by category
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for category, tests in test_suites.items():
            self.print_status(f"\n📋 Testing {category}:", "TITLE")
            self.print_status("-" * 40, "INFO")
            
            for test in tests:
                method, url, payload, description = test[:4]
                files = test[4] if len(test) > 4 else None
                
                result = self.test_endpoint(method, url, payload, files, description)
                total_tests += 1
                
                if result["success"]:
                    passed_tests += 1
                    status_color = "SUCCESS"
                    status_icon = "✅"
                else:
                    failed_tests += 1
                    status_color = "ERROR"
                    status_icon = "❌"
                
                # Print result
                response_time = f"({result['response_time']}s)" if result['response_time'] else ""
                status_code = f"[{result['status_code']}]" if result['status_code'] else "[ERROR]"
                
                self.print_status(
                    f"  {status_icon} {description} {status_code} {response_time}", 
                    status_color
                )
                
                if result["error"] and not result["status_code"] in [401, 422]:
                    self.print_status(f"      Error: {result['error']}", "WARNING")
                    
        # Print summary
        self.print_status("\n" + "=" * 60, "INFO")
        self.print_status("📊 TEST SUMMARY", "TITLE")
        self.print_status("=" * 60, "INFO")
        
        self.print_status(f"Total Tests: {total_tests}", "INFO")
        self.print_status(f"Passed: {passed_tests}", "SUCCESS")
        self.print_status(f"Failed: {failed_tests}", "ERROR")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        self.print_status(f"Success Rate: {success_rate:.1f}%", "SUCCESS" if success_rate > 80 else "WARNING")
        
        # Authentication status
        if self.token:
            self.print_status("🔐 Authentication: Active", "SUCCESS")
        else:
            self.print_status("🔐 Authentication: Not configured", "WARNING")
            
        # Save detailed results
        self.save_results()
        
    def save_results(self):
        """Save detailed test results to a JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.test_results),
            "passed": len([r for r in self.test_results if r["success"]]),
            "failed": len([r for r in self.test_results if not r["success"]]),
            "authentication_used": bool(self.token),
            "results": self.test_results
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2)
            self.print_status(f"💾 Detailed results saved to: {filename}", "SUCCESS")
        except Exception as e:
            self.print_status(f"❌ Could not save results: {e}", "ERROR")

def main():
    """Main execution function"""
    tester = MediTwinTester()
    
    tester.print_status("🏥 MediTwin Agents API Comprehensive Tester", "TITLE")
    tester.print_status("=" * 60, "INFO")
    tester.print_status(f"🔗 Login Service: {LOGIN_SERVICE_URL}", "INFO")
    tester.print_status(f"🔗 Agents Service: {AGENTS_SERVICE_URL}", "INFO")
    
    # Get authentication token
    if not tester.get_auth_token():
        tester.print_status("⚠️  Proceeding without authentication (some tests may fail)", "WARNING")
        input("Press Enter to continue...")
    
    # Run comprehensive tests
    tester.run_all_tests()
    
    tester.print_status("\n🎉 Testing completed!", "SUCCESS")

if __name__ == "__main__":
    main()
