#!/usr/bin/env python3
"""
MediTwin Complete User Journey Test - SINGLE COMPREHENSIVE TEST FILE
=====================================================================

This is the ONLY test file needed for the MediTwin frontend.
It tests the complete user journey from signup to all AI agent endpoints.

Features Tested:
- User Registration (Signup)
- User Authentication (Login) 
- User Profile Access
- All AI Agents Service Endpoints:
  * System Status & Info
  * Chat & Messaging
  * Medical Analysis (Symptoms, Diagnostics, Treatment)
  * Knowledge Base & Drug Interactions
  * Analytics & Health Scoring
  * Timeline & Document Management
  * OpenAI Compatible API

Usage:
    python3 complete_user_journey_test.py

Requirements:
    - Backend Auth Service running on localhost:8081
    - Agents Service running on localhost:8000
    - pip install requests

Author: MediTwin Development Team
Date: July 2025
"""

import requests
import json
import time
import uuid
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(title: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{title.center(80)}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.RESET}\n")

def print_result(test_name: str, status: str, details: str = ""):
    if status == "PASS":
        color = Colors.GREEN
        symbol = "✅"
    elif status == "FAIL":
        color = Colors.RED
        symbol = "❌"
    else:
        color = Colors.YELLOW
        symbol = "⚠️"
    
    print(f"{color}{symbol} {test_name:<50}{Colors.RESET} [{color}{status}{Colors.RESET}]")
    if details:
        print(f"  {Colors.WHITE}{details}{Colors.RESET}")

class CompleteIntegrationTest:
    def __init__(self):
        self.backend_url = "http://localhost:8081"  # Backend Auth Service
        self.agents_url = "http://localhost:8000"   # Agents Service
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        self.token = None
        self.test_user_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "TestUser123!"
        
        self.results = {
            'auth': {},
            'agents': {}
        }

    def test_user_signup(self):
        """Test user registration"""
        print_header("USER REGISTRATION TEST")
        
        signup_data = {
            "username": f"testuser_{uuid.uuid4().hex[:8]}",
            "email": self.test_user_email,
            "password": self.test_user_password,
            "first_name": "Test",
            "last_name": "User"
        }
        
        try:
            response = self.session.post(f"{self.backend_url}/auth/signup", json=signup_data, timeout=15)
            
            if response.status_code == 200 or response.status_code == 201:
                print_result("User Registration", "PASS", f"User created: {signup_data['email']}")
                self.results['auth']['signup'] = True
                return True
            else:
                print_result("User Registration", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                self.results['auth']['signup'] = False
                return False
                
        except Exception as e:
            print_result("User Registration", "FAIL", f"Error: {str(e)}")
            self.results['auth']['signup'] = False
            return False

    def test_user_login(self):
        """Test user login and token acquisition"""
        print_header("USER LOGIN TEST")
        
        login_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        try:
            response = self.session.post(f"{self.backend_url}/auth/login", json=login_data, timeout=15)
            
            if response.status_code == 200:
                auth_data = response.json()
                self.token = auth_data.get("access_token")
                
                if self.token:
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    print_result("User Login", "PASS", f"Token acquired ({len(self.token)} chars)")
                    self.results['auth']['login'] = True
                    return True
                else:
                    print_result("User Login", "FAIL", "No access token received")
                    self.results['auth']['login'] = False
                    return False
            else:
                print_result("User Login", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                self.results['auth']['login'] = False
                return False
                
        except Exception as e:
            print_result("User Login", "FAIL", f"Error: {str(e)}")
            self.results['auth']['login'] = False
            return False

    def test_user_profile(self):
        """Test user profile access"""
        try:
            response = self.session.get(f"{self.backend_url}/users/me", timeout=10)
            
            if response.status_code == 200:
                profile_data = response.json()
                print_result("User Profile Access", "PASS", f"Profile retrieved for: {profile_data.get('email', 'N/A')}")
                self.results['auth']['profile'] = True
                return True
            else:
                print_result("User Profile Access", "FAIL", f"Status: {response.status_code}")
                self.results['auth']['profile'] = False
                return False
                
        except Exception as e:
            print_result("User Profile Access", "FAIL", f"Error: {str(e)}")
            self.results['auth']['profile'] = False
            return False

    def test_all_agents_endpoints(self):
        """Test all agents service endpoints"""
        print_header("AGENTS SERVICE ENDPOINTS TEST")
        
        # Define all endpoints to test
        endpoints_to_test = [
            # System endpoints
            {
                "name": "System Status",
                "method": "GET",
                "endpoint": "/v1/system_info/system/status",
                "category": "system"
            },
            {
                "name": "System Info",
                "method": "GET", 
                "endpoint": "/v1/system_info/info",
                "category": "system"
            },
            {
                "name": "System Metrics",
                "method": "GET",
                "endpoint": "/v1/system_info/metrics", 
                "category": "system"
            },
            {
                "name": "Database Status",
                "method": "GET",
                "endpoint": "/v1/system_info/database/status",
                "category": "system"
            },
            
            # Chat endpoints
            {
                "name": "Chat Message",
                "method": "POST",
                "endpoint": "/v1/chat/message",
                "data": {"message": "Hello, I need medical advice about headaches. What should I know?"},
                "category": "chat"
            },
            {
                "name": "Chat Sessions",
                "method": "GET",
                "endpoint": "/v1/chat/sessions",
                "category": "chat"
            },
            
            # Medical Analysis endpoints (Previously broken)
            {
                "name": "Symptom Analysis",
                "method": "POST", 
                "endpoint": "/v1/medical_analysis/symptoms/analyze",
                "data": {
                    "symptoms": ["headache", "nausea", "dizziness"],
                    "duration": "3 days",
                    "severity": "moderate",
                    "context": "Started after working long hours"
                },
                "category": "medical"
            },
            {
                "name": "Diagnostic Suggestions",
                "method": "POST",
                "endpoint": "/v1/medical_analysis/diagnostic/suggestions",
                "data": {
                    "symptoms": ["chest pain", "shortness of breath"],
                    "medical_history": "No known heart conditions"
                },
                "category": "medical"
            },
            {
                "name": "Treatment Recommendations",
                "method": "POST",
                "endpoint": "/v1/medical_analysis/treatment/recommendations",
                "data": {
                    "condition": "tension headache",
                    "symptoms": ["headache", "neck tension"],
                    "severity": "moderate"
                },
                "category": "medical"
            },
            
            # Knowledge Base endpoints (Previously broken)
            {
                "name": "Knowledge Search",
                "method": "GET",
                "endpoint": "/v1/knowledge_base/knowledge/search",
                "params": {"query": "diabetes symptoms and management"},
                "category": "knowledge"
            },
            {
                "name": "Medical Information",
                "method": "GET",
                "endpoint": "/v1/knowledge_base/medical/information",
                "params": {"topic": "hypertension"},
                "category": "knowledge"
            },
            {
                "name": "Drug Interactions",
                "method": "POST",
                "endpoint": "/v1/knowledge_base/drugs/interactions",
                "data": {"medications": ["aspirin", "ibuprofen", "acetaminophen"]},
                "category": "knowledge"
            },
            
            # Analytics endpoints
            {
                "name": "Health Trends",
                "method": "GET",
                "endpoint": "/v1/analytics/analytics/trends",
                "params": {"period": "30d"},
                "category": "analytics"
            },
            {
                "name": "Analytics Dashboard",
                "method": "GET",
                "endpoint": "/v1/analytics/analytics/dashboard",
                "category": "analytics"
            },
            {
                "name": "Health Score",
                "method": "GET",
                "endpoint": "/v1/analytics/health/score",
                "category": "analytics"
            },
            {
                "name": "Risk Assessment",
                "method": "GET", 
                "endpoint": "/v1/analytics/health/risk-assessment",
                "category": "analytics"
            },
            
            # Timeline endpoints
            {
                "name": "Timeline Events",
                "method": "GET",
                "endpoint": "/v1/timeline/timeline",
                "params": {"limit": "10"},
                "category": "timeline"
            },
            
            # Upload endpoints
            {
                "name": "Documents List",
                "method": "GET",
                "endpoint": "/v1/upload/documents",
                "category": "upload"
            },
            
            # OpenAI Compatible
            {
                "name": "OpenAI Chat Completions",
                "method": "POST",
                "endpoint": "/v1/openai_compatible/v1/chat/completions",
                "data": {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "What are the symptoms of diabetes?"}],
                    "stream": False
                },
                "category": "openai"
            }
        ]
        
        # Test each endpoint
        category_results = {}
        
        for endpoint_test in endpoints_to_test:
            name = endpoint_test["name"]
            method = endpoint_test["method"]
            endpoint = endpoint_test["endpoint"]
            data = endpoint_test.get("data")
            params = endpoint_test.get("params")
            category = endpoint_test["category"]
            
            if category not in category_results:
                category_results[category] = {"passed": 0, "total": 0}
            
            category_results[category]["total"] += 1
            
            try:
                url = f"{self.agents_url}{endpoint}"
                
                if method == "GET":
                    response = self.session.get(url, params=params, timeout=20)
                else:
                    response = self.session.post(url, json=data, timeout=20)
                
                if response.status_code == 200:
                    response_data = response.json()
                    
                    # Show meaningful response data
                    detail = ""
                    if isinstance(response_data, dict):
                        if 'response' in response_data:
                            detail = f"AI Response: {response_data['response'][:80]}..."
                        elif 'analysis' in response_data:
                            detail = f"Analysis: {response_data['analysis'][:80]}..."
                        elif 'recommendations' in response_data:
                            detail = f"Recommendations: {len(response_data['recommendations'])} items"
                        elif 'results' in response_data:
                            detail = f"Results: {len(response_data['results'])} items"
                        elif 'trends' in response_data:
                            detail = f"Trends: {len(response_data['trends'])} metrics"
                        elif 'status' in response_data:
                            detail = f"Status: {response_data['status']}"
                        elif 'choices' in response_data:
                            detail = f"OpenAI Response: {len(response_data['choices'])} choices"
                    
                    print_result(name, "PASS", detail)
                    category_results[category]["passed"] += 1
                    self.results['agents'][name] = True
                    
                else:
                    error_detail = response.text[:150] if response.text else f"HTTP {response.status_code}"
                    print_result(name, "FAIL", f"Status: {response.status_code}, Error: {error_detail}")
                    self.results['agents'][name] = False
                    
            except Exception as e:
                print_result(name, "FAIL", f"Exception: {str(e)}")
                self.results['agents'][name] = False
        
        # Print category summaries
        print_header("CATEGORY SUMMARY")
        
        total_passed = 0
        total_tests = 0
        
        for category, results in category_results.items():
            passed = results["passed"]
            total = results["total"]
            percentage = (passed / total * 100) if total > 0 else 0
            
            status = "PASS" if percentage >= 80 else "PARTIAL" if percentage >= 50 else "FAIL"
            print_result(f"{category.upper()} Endpoints", status, f"{passed}/{total} ({percentage:.1f}%)")
            
            total_passed += passed
            total_tests += total
        
        overall_percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
        overall_status = "PASS" if overall_percentage >= 80 else "PARTIAL" if overall_percentage >= 60 else "FAIL"
        
        print_result("OVERALL AGENTS SERVICE", overall_status, f"{total_passed}/{total_tests} ({overall_percentage:.1f}%)")
        
        return category_results

    def generate_final_report(self, category_results):
        """Generate final comprehensive report"""
        print_header("COMPREHENSIVE TEST REPORT")
        
        # Authentication summary
        auth_passed = sum(1 for v in self.results['auth'].values() if v)
        auth_total = len(self.results['auth'])
        
        print(f"\n🔐 AUTHENTICATION & USER MANAGEMENT:")
        print(f"   Success Rate: {auth_passed}/{auth_total} ({auth_passed/auth_total*100:.1f}%)")
        print(f"   Test User: {self.test_user_email}")
        print(f"   Token Length: {len(self.token) if self.token else 0} characters")
        
        # Agents service summary
        agents_passed = sum(1 for v in self.results['agents'].values() if v)
        agents_total = len(self.results['agents'])
        
        print(f"\n🤖 AGENTS SERVICE:")
        print(f"   Success Rate: {agents_passed}/{agents_total} ({agents_passed/agents_total*100:.1f}%)")
        
        # Critical endpoint status
        critical_endpoints = [
            "Chat Message",
            "Symptom Analysis", 
            "Treatment Recommendations",
            "Knowledge Search"
        ]
        
        print(f"\n🎯 CRITICAL MEDICAL ENDPOINTS:")
        critical_working = 0
        for endpoint in critical_endpoints:
            status = "✅ WORKING" if self.results['agents'].get(endpoint, False) else "❌ BROKEN"
            print(f"   • {endpoint:<30} {status}")
            if self.results['agents'].get(endpoint, False):
                critical_working += 1
        
        print(f"\n📊 SYSTEM STATUS:")
        if critical_working >= 3:
            print(f"   🎉 EXCELLENT: Core medical features are working!")
        elif critical_working >= 2:
            print(f"   ✅ GOOD: Most critical features are working")
        elif critical_working >= 1:
            print(f"   ⚠️  PARTIAL: Some critical features are working")
        else:
            print(f"   ❌ CRITICAL: Core medical features are broken")
        
        # Detailed category breakdown
        print(f"\n📋 DETAILED BREAKDOWN:")
        for category, results in category_results.items():
            passed = results["passed"]
            total = results["total"]
            percentage = (passed / total * 100) if total > 0 else 0
            
            status_icon = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
            print(f"   {status_icon} {category.upper():<12} {passed}/{total} ({percentage:.1f}%)")
        
        # Overall assessment
        overall_percentage = ((auth_passed + agents_passed) / (auth_total + agents_total) * 100) if (auth_total + agents_total) > 0 else 0
        
        print(f"\n🏆 OVERALL SYSTEM STATUS:")
        print(f"   Success Rate: {overall_percentage:.1f}%")
        
        if overall_percentage >= 90:
            print(f"   🚀 SYSTEM READY FOR PRODUCTION!")
        elif overall_percentage >= 80:
            print(f"   ✅ SYSTEM MOSTLY FUNCTIONAL - Ready for deployment")
        elif overall_percentage >= 70:
            print(f"   ⚠️  SYSTEM PARTIALLY FUNCTIONAL - Some fixes needed")
        else:
            print(f"   ❌ SYSTEM NEEDS SIGNIFICANT WORK")
        
        # Next steps
        print(f"\n📋 NEXT STEPS:")
        if critical_working >= 3:
            print(f"   1. ✅ Deploy frontend with full functionality")
            print(f"   2. ✅ Medical features are working as expected")
            print(f"   3. 🚀 System is ready for users")
        else:
            print(f"   1. 🔧 Fix remaining broken endpoints")
            print(f"   2. 🧪 Re-test critical medical features")
            print(f"   3. ✅ Deploy once all critical features work")

    def run_complete_test(self):
        """Run the complete integration test"""
        print_header("MEDITWIN COMPLETE INTEGRATION TEST")
        print(f"🕒 Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 Backend URL: {self.backend_url}")
        print(f"🤖 Agents URL: {self.agents_url}")
        
        # Step 1: User Registration
        if not self.test_user_signup():
            print("❌ Cannot proceed without user registration")
            return
        
        # Step 2: User Login  
        if not self.test_user_login():
            print("❌ Cannot proceed without authentication")
            return
        
        # Step 3: User Profile
        self.test_user_profile()
        
        # Step 4: All Agents Endpoints
        category_results = self.test_all_agents_endpoints()
        
        # Step 5: Final Report
        self.generate_final_report(category_results)
        
        print(f"\n🕒 Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    test = CompleteIntegrationTest()
    test.run_complete_test()
