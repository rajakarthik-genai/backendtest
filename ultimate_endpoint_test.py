#!/usr/bin/env python3
"""
Ultimate Comprehensive Endpoint Testing Script

This script tests all MediTwin backend endpoints with proper sample data,
including fixing the remaining failing tests.
"""

import asyncio
import json
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid
import os
import sys
import io
import base64

# Add project path
sys.path.append('/home/user/agents/meditwin-agents')

BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

class UltimateEndpointTester:
    """Test all endpoints with comprehensive sample data and fixes."""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        self.test_session_id = f"session_{uuid.uuid4().hex[:8]}"
        self.test_conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
        self.test_token = None
        self.test_results = {}
        self.created_event_id = None
        
        # Sample data with proper formatting
        self.sample_data = {
            "user_signup": {
                "email": f"testuser{uuid.uuid4().hex[:6]}@example.com",
                "username": f"testuser{uuid.uuid4().hex[:6]}",
                "password": "SecurePass123!",
                "full_name": "Test User"
            },
            "timeline_event": {
                "event_type": "medical",
                "title": "Blood Pressure Check",
                "description": "Routine blood pressure measurement during checkup",
                "timestamp": datetime.now().isoformat(),
                "severity": "medium",
                "metadata": json.dumps({
                    "systolic": 130,
                    "diastolic": 85,
                    "pulse": 72,
                    "location": "clinic"
                })
            },
            "chat_message": {
                "message": "I've been experiencing chest pain after exercise. Should I be concerned?",
                "session_id": self.test_session_id,
                "include_context": True
            },
            "expert_query": {
                "message": "Patient has chest pain, shortness of breath, and elevated blood pressure. Please provide cardiology consultation.",
                "specialties": ["cardiology", "internal_medicine"],
                "include_context": True,
                "priority": "high"
            }
        }
    
    def create_test_image(self):
        """Create a simple test image in memory."""
        # Create a minimal PNG image (1x1 pixel)
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jINVB"
            "AAAAABJRU5ErkJggg=="
        )
        return io.BytesIO(png_data)
    
    def log_test_result(self, endpoint: str, method: str, status_code: int, 
                       success: bool, error_msg: str = None, response_data: Any = None):
        """Log test result."""
        result = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "error": error_msg,
            "response_preview": str(response_data)[:200] if response_data else None
        }
        
        if endpoint not in self.test_results:
            self.test_results[endpoint] = []
        self.test_results[endpoint].append(result)
        
        # Print result
        status_emoji = "✅" if success else "❌"
        print(f"{status_emoji} {method} {endpoint} - {status_code}")
        if error_msg:
            print(f"   Error: {error_msg}")
        elif response_data:
            print(f"   Response: {str(response_data)[:100]}...")
    
    async def test_health_endpoints(self):
        """Test health check endpoints."""
        print("\n🏥 Testing Health Endpoints")
        print("=" * 50)
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test basic health check
            try:
                response = await client.get(f"{self.base_url}/")
                success = response.status_code == 200
                self.log_test_result("/", "GET", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
            except Exception as e:
                self.log_test_result("/", "GET", 0, False, str(e))
            
            # Test detailed health check
            try:
                response = await client.get(f"{self.base_url}/health")
                success = response.status_code == 200
                self.log_test_result("/health", "GET", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
            except Exception as e:
                self.log_test_result("/health", "GET", 0, False, str(e))
    
    async def test_auth_endpoints(self):
        """Test authentication endpoints."""
        print("\n🔐 Testing Authentication Endpoints")
        print("=" * 50)
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test user signup
            try:
                response = await client.post(f"{self.base_url}/auth/signup", 
                                           json=self.sample_data["user_signup"])
                success = response.status_code in [200, 201]
                self.log_test_result("/auth/signup", "POST", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
                
                # Store token if successful
                if success:
                    response_data = response.json()
                    self.test_token = response_data.get("access_token")
                    
            except Exception as e:
                self.log_test_result("/auth/signup", "POST", 0, False, str(e))
            
            # Test user login
            try:
                login_data = {
                    "email": self.sample_data["user_signup"]["email"],
                    "password": self.sample_data["user_signup"]["password"]
                }
                response = await client.post(f"{self.base_url}/auth/login", json=login_data)
                success = response.status_code == 200
                self.log_test_result("/auth/login", "POST", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
                
                # Store token if successful
                if success:
                    response_data = response.json()
                    self.test_token = response_data.get("access_token")
                    
            except Exception as e:
                self.log_test_result("/auth/login", "POST", 0, False, str(e))
            
            # Test user profile (if we have a token)
            if self.test_token:
                try:
                    headers = {"Authorization": f"Bearer {self.test_token}"}
                    response = await client.get(f"{self.base_url}/auth/me", headers=headers)
                    success = response.status_code == 200
                    self.log_test_result("/auth/me", "GET", response.status_code, success,
                                       None if success else response.text, response.json() if success else None)
                except Exception as e:
                    self.log_test_result("/auth/me", "GET", 0, False, str(e))
    
    async def test_timeline_endpoints(self):
        """Test timeline endpoints."""
        print("\n📅 Testing Timeline Endpoints")
        print("=" * 50)
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test get timeline
            try:
                response = await client.get(f"{self.base_url}/timeline/")
                success = response.status_code == 200
                self.log_test_result("/timeline/", "GET", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
            except Exception as e:
                self.log_test_result("/timeline/", "GET", 0, False, str(e))
            
            # Test create timeline event (as form data)
            try:
                form_data = {
                    "event_type": self.sample_data["timeline_event"]["event_type"],
                    "title": self.sample_data["timeline_event"]["title"],
                    "description": self.sample_data["timeline_event"]["description"],
                    "timestamp": self.sample_data["timeline_event"]["timestamp"],
                    "severity": self.sample_data["timeline_event"]["severity"],
                    "metadata": self.sample_data["timeline_event"]["metadata"]
                }
                
                response = await client.post(f"{self.base_url}/timeline/event", data=form_data)
                success = response.status_code == 200
                self.log_test_result("/timeline/event", "POST", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
            except Exception as e:
                self.log_test_result("/timeline/event", "POST", 0, False, str(e))
            
            # Test timeline summary
            try:
                response = await client.get(f"{self.base_url}/timeline/summary?days=30")
                success = response.status_code == 200
                self.log_test_result("/timeline/summary", "GET", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
            except Exception as e:
                self.log_test_result("/timeline/summary", "GET", 0, False, str(e))
            
            # Test timeline search
            try:
                response = await client.get(f"{self.base_url}/timeline/search?search_term=chest")
                success = response.status_code == 200
                self.log_test_result("/timeline/search", "GET", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
            except Exception as e:
                self.log_test_result("/timeline/search", "GET", 0, False, str(e))
    
    async def test_chat_endpoints(self):
        """Test chat endpoints."""
        print("\n💬 Testing Chat Endpoints")
        print("=" * 50)
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test chat message
            try:
                response = await client.post(f"{self.base_url}/chat/message", 
                                           json=self.sample_data["chat_message"])
                success = response.status_code == 200
                self.log_test_result("/chat/message", "POST", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
            except Exception as e:
                self.log_test_result("/chat/message", "POST", 0, False, str(e))
            
            # Test chat streaming
            try:
                response = await client.post(f"{self.base_url}/chat/stream", 
                                           json=self.sample_data["chat_message"])
                success = response.status_code == 200
                self.log_test_result("/chat/stream", "POST", response.status_code, success,
                                   None if success else response.text, "Streaming response" if success else None)
            except Exception as e:
                self.log_test_result("/chat/stream", "POST", 0, False, str(e))
            
            # Test chat history with session ID
            try:
                response = await client.get(f"{self.base_url}/chat/history/{self.test_session_id}")
                success = response.status_code == 200
                self.log_test_result(f"/chat/history/{self.test_session_id}", "GET", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
            except Exception as e:
                self.log_test_result(f"/chat/history/{self.test_session_id}", "GET", 0, False, str(e))
            
            # Test chat sessions
            try:
                response = await client.get(f"{self.base_url}/chat/sessions")
                success = response.status_code == 200
                self.log_test_result("/chat/sessions", "GET", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
            except Exception as e:
                self.log_test_result("/chat/sessions", "GET", 0, False, str(e))
    
    async def test_expert_opinion_endpoints(self):
        """Test expert opinion endpoints."""
        print("\n👨‍⚕️ Testing Expert Opinion Endpoints")
        print("=" * 50)
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test expert opinion
            try:
                response = await client.post(f"{self.base_url}/expert/opinion", 
                                           json=self.sample_data["expert_query"])
                success = response.status_code == 200
                self.log_test_result("/expert/opinion", "POST", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
            except Exception as e:
                self.log_test_result("/expert/opinion", "POST", 0, False, str(e))
            
            # Test specialties
            try:
                response = await client.get(f"{self.base_url}/expert/specialties")
                success = response.status_code == 200
                self.log_test_result("/expert/specialties", "GET", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
            except Exception as e:
                self.log_test_result("/expert/specialties", "GET", 0, False, str(e))
    
    async def test_anatomy_endpoints(self):
        """Test anatomy endpoints."""
        print("\n🫀 Testing Anatomy Endpoints")
        print("=" * 50)
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test anatomy overview
            try:
                response = await client.get(f"{self.base_url}/anatomy/")
                success = response.status_code == 200
                self.log_test_result("/anatomy/", "GET", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
            except Exception as e:
                self.log_test_result("/anatomy/", "GET", 0, False, str(e))
            
            # Test organ timeline
            try:
                response = await client.get(f"{self.base_url}/anatomy/heart/timeline")
                success = response.status_code == 200
                self.log_test_result("/anatomy/heart/timeline", "GET", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
            except Exception as e:
                self.log_test_result("/anatomy/heart/timeline", "GET", 0, False, str(e))
    
    async def test_events_endpoints(self):
        """Test medical events endpoints."""
        print("\n📋 Testing Events Endpoints")
        print("=" * 50)
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test get events with user_id parameter
            try:
                response = await client.get(f"{self.base_url}/events/?user_id={self.test_user_id}")
                success = response.status_code == 200
                self.log_test_result("/events/", "GET", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
            except Exception as e:
                self.log_test_result("/events/", "GET", 0, False, str(e))
            
            # Test create event with minimal required fields
            try:
                event_data = {
                    "user_id": self.test_user_id,
                    "event_type": "medical",
                    "title": "Test Medical Event",
                    "description": "Test event for comprehensive testing",
                    "timestamp": datetime.now().isoformat(),
                    "severity": "medium"
                }
                
                response = await client.post(f"{self.base_url}/events/", json=event_data)
                success = response.status_code == 201
                self.log_test_result("/events/", "POST", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
                
                # Store event ID for later tests
                if success:
                    response_data = response.json()
                    self.created_event_id = response_data.get("event_id")
                    
            except Exception as e:
                self.log_test_result("/events/", "POST", 0, False, str(e))
            
            # Test get specific event (if we created one)
            if self.created_event_id:
                try:
                    response = await client.get(f"{self.base_url}/events/{self.created_event_id}?user_id={self.test_user_id}")
                    success = response.status_code == 200
                    self.log_test_result(f"/events/{self.created_event_id}", "GET", response.status_code, success,
                                       None if success else response.text, response.json() if success else None)
                except Exception as e:
                    self.log_test_result(f"/events/{self.created_event_id}", "GET", 0, False, str(e))
    
    async def test_upload_endpoints(self):
        """Test upload endpoints."""
        print("\n📤 Testing Upload Endpoints")
        print("=" * 50)
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test document upload with proper image file
            try:
                # Create a test image
                test_image = self.create_test_image()
                
                files = {
                    "file": ("test_image.png", test_image, "image/png")
                }
                
                data = {
                    "document_type": "medical_report",
                    "title": "Test Medical Image",
                    "description": "Test image for upload testing"
                }
                
                response = await client.post(f"{self.base_url}/upload/document", 
                                           files=files, data=data)
                success = response.status_code == 200
                self.log_test_result("/upload/document", "POST", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
            except Exception as e:
                self.log_test_result("/upload/document", "POST", 0, False, str(e))
            
            # Test get documents
            try:
                response = await client.get(f"{self.base_url}/upload/documents")
                success = response.status_code == 200
                self.log_test_result("/upload/documents", "GET", response.status_code, success,
                                   None if success else response.text, response.json() if success else None)
            except Exception as e:
                self.log_test_result("/upload/documents", "GET", 0, False, str(e))
    
    async def test_api_documentation(self):
        """Test API documentation endpoints."""
        print("\n📚 Testing API Documentation")
        print("=" * 50)
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            # Test Swagger UI
            try:
                response = await client.get(f"{self.base_url}/docs")
                success = response.status_code == 200
                self.log_test_result("/docs", "GET", response.status_code, success,
                                   None if success else response.text, None)
            except Exception as e:
                self.log_test_result("/docs", "GET", 0, False, str(e))
            
            # Test ReDoc
            try:
                response = await client.get(f"{self.base_url}/redoc")
                success = response.status_code == 200
                self.log_test_result("/redoc", "GET", response.status_code, success,
                                   None if success else response.text, None)
            except Exception as e:
                self.log_test_result("/redoc", "GET", 0, False, str(e))
            
            # Test OpenAPI schema
            try:
                response = await client.get(f"{self.base_url}/openapi.json")
                success = response.status_code == 200
                self.log_test_result("/openapi.json", "GET", response.status_code, success,
                                   None if success else response.text, None)
            except Exception as e:
                self.log_test_result("/openapi.json", "GET", 0, False, str(e))
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n📊 Test Results Summary")
        print("=" * 80)
        
        total_tests = sum(len(results) for results in self.test_results.values())
        successful_tests = sum(1 for results in self.test_results.values() 
                             for result in results if result["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        print(f"\n📋 Detailed Results by Endpoint:")
        print("-" * 80)
        
        for endpoint, results in self.test_results.items():
            print(f"\n{endpoint}:")
            for result in results:
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                print(f"  {result['method']} - {status} ({result['status_code']})")
                if result["error"]:
                    print(f"    Error: {result['error']}")
        
        # Save detailed report to file
        report_file = f"ultimate_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Create summary report
        summary_file = f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(summary_file, 'w') as f:
            f.write("# MediTwin Backend - Ultimate Test Results\n\n")
            f.write(f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Total Tests:** {total_tests}\n")
            f.write(f"**Successful:** {successful_tests} ✅\n")
            f.write(f"**Failed:** {failed_tests} ❌\n")
            f.write(f"**Success Rate:** {(successful_tests/total_tests)*100:.1f}%\n\n")
            
            f.write("## Test Details\n\n")
            for endpoint, results in self.test_results.items():
                f.write(f"### {endpoint}\n\n")
                for result in results:
                    status = "✅ PASS" if result["success"] else "❌ FAIL"
                    f.write(f"- **{result['method']}** - {status} ({result['status_code']})\n")
                    if result["error"]:
                        f.write(f"  - Error: {result['error']}\n")
                f.write("\n")
        
        print(f"📄 Summary report saved to: {summary_file}")
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": (successful_tests/total_tests)*100 if total_tests > 0 else 0
        }
    
    async def run_all_tests(self):
        """Run all endpoint tests."""
        print("🧪 MediTwin Backend - Ultimate Comprehensive Endpoint Testing")
        print("=" * 80)
        print(f"Test User ID: {self.test_user_id}")
        print(f"Test Session ID: {self.test_session_id}")
        print(f"Base URL: {self.base_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # Run all test suites
        await self.test_health_endpoints()
        await self.test_auth_endpoints()
        await self.test_timeline_endpoints()
        await self.test_chat_endpoints()
        await self.test_expert_opinion_endpoints()
        await self.test_anatomy_endpoints()
        await self.test_events_endpoints()
        await self.test_upload_endpoints()
        await self.test_api_documentation()
        
        # Generate and display report
        return self.generate_test_report()


async def main():
    """Main test runner."""
    tester = UltimateEndpointTester()
    report = await tester.run_all_tests()
    
    print(f"\n🎯 Testing Complete!")
    print(f"Overall Success Rate: {report['success_rate']:.1f}%")
    
    if report['failed_tests'] > 0:
        print(f"⚠️  {report['failed_tests']} tests failed - check the detailed results above")
        return 1
    else:
        print("🎉 All tests passed!")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
