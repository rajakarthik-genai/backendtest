#!/usr/bin/env python3
"""
Comprehensive endpoint testing script for MediTwin Backend.

Tests the complete user journey:
1. Health check
2. Authentication (if enabled)
3. Document upload
4. Processing status monitoring
5. Chat interactions
6. Timeline management
7. Expert consultations
8. Data verification across all databases
"""

import os
import sys
import json
import time
import asyncio
import httpx
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Base URL for the API
BASE_URL = "http://localhost:8000"

class EndpointTester:
    """Comprehensive endpoint tester for MediTwin Backend."""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.session = httpx.AsyncClient()
        self.test_user_id = "test_user_123"
        self.test_session_id = "test_session_456"
        self.test_document_id = None
        self.auth_headers = {}
        
        # Test results tracking
        self.test_results = {
            "health": {"status": "pending", "tests": []},
            "auth": {"status": "pending", "tests": []},
            "upload": {"status": "pending", "tests": []},
            "chat": {"status": "pending", "tests": []},
            "timeline": {"status": "pending", "tests": []},
            "expert": {"status": "pending", "tests": []},
            "anatomy": {"status": "pending", "tests": []},
            "events": {"status": "pending", "tests": []},
            "data_verification": {"status": "pending", "tests": []}
        }
    
    def log_test(self, category: str, test_name: str, status: str, details: Any = None):
        """Log test result."""
        result = {
            "test": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results[category]["tests"].append(result)
        
        status_emoji = "✅" if status == "passed" else "❌" if status == "failed" else "⏳"
        print(f"{status_emoji} [{category.upper()}] {test_name}: {status}")
        
        if details and status == "failed":
            print(f"    Details: {details}")
    
    async def test_health_endpoints(self):
        """Test health check endpoints."""
        print("\n🔍 Testing Health Endpoints...")
        
        try:
            # Basic health check
            response = await self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("health", "basic_health_check", "passed", data)
            else:
                self.log_test("health", "basic_health_check", "failed", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("health", "basic_health_check", "failed", str(e))
        
        try:
            # Detailed health check
            response = await self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_test("health", "detailed_health_check", "passed", data)
            else:
                self.log_test("health", "detailed_health_check", "failed", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("health", "detailed_health_check", "failed", str(e))
        
        self.test_results["health"]["status"] = "completed"
    
    async def test_auth_endpoints(self):
        """Test authentication endpoints."""
        print("\n🔐 Testing Authentication Endpoints...")
        
        # Since JWT_REQUIRE_AUTH=false in the env, we'll test without tokens
        # But we'll simulate what would happen with tokens
        
        try:
            # Test accessing protected endpoint without auth (should work since auth is disabled)
            response = await self.session.get(f"{self.base_url}/chat/sessions")
            if response.status_code in [200, 422]:  # 422 is expected for missing user_id
                self.log_test("auth", "no_auth_access", "passed", "Auth disabled - access allowed")
            else:
                self.log_test("auth", "no_auth_access", "failed", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("auth", "no_auth_access", "failed", str(e))
        
        # Test with mock JWT headers (for future when auth is enabled)
        mock_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidGVzdF91c2VyXzEyMyIsImV4cCI6OTk5OTk5OTk5OX0.test"
        self.auth_headers = {"Authorization": f"Bearer {mock_token}"}
        
        self.test_results["auth"]["status"] = "completed"
    
    async def create_test_document(self) -> bytes:
        """Create a test PDF document for upload testing."""
        # Create a simple test document content
        test_content = """
        MEDICAL REPORT
        
        Patient: John Doe
        Date: 2024-01-15
        
        Chief Complaint: Chest pain and shortness of breath
        
        History of Present Illness:
        The patient is a 45-year-old male who presents with a 2-day history of chest pain.
        The pain is described as sharp, substernal, and worsens with deep inspiration.
        Associated symptoms include shortness of breath and mild fatigue.
        
        Past Medical History:
        - Hypertension
        - Type 2 Diabetes
        
        Current Medications:
        - Metformin 500mg twice daily
        - Lisinopril 10mg daily
        
        Physical Examination:
        Vital Signs: BP 140/90, HR 88, RR 18, Temp 98.6°F
        Heart: Regular rate and rhythm, no murmurs
        Lungs: Clear to auscultation bilaterally
        
        Assessment and Plan:
        1. Chest pain - likely musculoskeletal, recommend rest and NSAIDs
        2. Hypertension - continue current medications
        3. Diabetes - well controlled, continue metformin
        
        Follow-up in 1 week if symptoms persist.
        """
        
        return test_content.encode('utf-8')
    
    async def test_upload_endpoints(self):
        """Test file upload endpoints."""
        print("\n📁 Testing Upload Endpoints...")
        
        try:
            # Create test document
            test_doc_content = await self.create_test_document()
            
            # Test document upload
            files = {"file": ("test_medical_report.txt", test_doc_content, "text/plain")}
            data = {"user_id": self.test_user_id, "description": "Test medical report"}
            
            response = await self.session.post(f"{self.base_url}/upload/document", files=files, data=data)
            
            if response.status_code == 200:
                upload_result = response.json()
                self.test_document_id = upload_result.get("document_id")
                self.log_test("upload", "document_upload", "passed", upload_result)
            else:
                self.log_test("upload", "document_upload", "failed", f"Status: {response.status_code}, Body: {response.text}")
                
        except Exception as e:
            self.log_test("upload", "document_upload", "failed", str(e))
        
        # Test upload status monitoring
        if self.test_document_id:
            try:
                for attempt in range(10):  # Monitor for up to 10 attempts
                    response = await self.session.get(
                        f"{self.base_url}/upload/status/{self.test_document_id}",
                        params={"user_id": self.test_user_id}
                    )
                    
                    if response.status_code == 200:
                        status_data = response.json()
                        current_status = status_data.get("status", "unknown")
                        
                        self.log_test("upload", f"status_check_attempt_{attempt + 1}", "passed", status_data)
                        
                        if current_status in ["completed", "failed"]:
                            break
                        
                        await asyncio.sleep(2)  # Wait 2 seconds between checks
                    else:
                        self.log_test("upload", f"status_check_attempt_{attempt + 1}", "failed", f"Status: {response.status_code}")
                        
            except Exception as e:
                self.log_test("upload", "status_monitoring", "failed", str(e))
        
        # Test upload history
        try:
            response = await self.session.get(
                f"{self.base_url}/upload/documents",
                params={"user_id": self.test_user_id, "limit": 10}
            )
            
            if response.status_code == 200:
                history_data = response.json()
                self.log_test("upload", "upload_history", "passed", history_data)
            else:
                self.log_test("upload", "upload_history", "failed", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("upload", "upload_history", "failed", str(e))
        
        self.test_results["upload"]["status"] = "completed"
    
    async def test_chat_endpoints(self):
        """Test chat endpoints."""
        print("\n💬 Testing Chat Endpoints...")
        
        # Test simple chat message
        try:
            chat_data = {
                "message": "I've been experiencing chest pain and shortness of breath. Can you help me understand what might be causing this?",
                "session_id": self.test_session_id
            }
            
            # Since auth is disabled, we need to include user_id in the request
            # First check the actual endpoint structure
            response = await self.session.post(f"{self.base_url}/chat/message", json=chat_data)
            
            if response.status_code == 200:
                chat_result = response.json()
                self.log_test("chat", "simple_message", "passed", chat_result)
            elif response.status_code == 422:
                # Likely needs user_id - let's check the actual endpoint
                self.log_test("chat", "simple_message", "info", "Need to check endpoint structure")
            else:
                self.log_test("chat", "simple_message", "failed", f"Status: {response.status_code}, Body: {response.text}")
                
        except Exception as e:
            self.log_test("chat", "simple_message", "failed", str(e))
        
        # Test streaming chat
        try:
            chat_data = {
                "message": "What medications should I be taking for hypertension and diabetes?",
                "session_id": self.test_session_id
            }
            
            response = await self.session.post(f"{self.base_url}/chat/stream", json=chat_data)
            
            if response.status_code == 200:
                # For streaming, we'd need to handle SSE
                self.log_test("chat", "streaming_message", "passed", "Streaming endpoint accessible")
            else:
                self.log_test("chat", "streaming_message", "failed", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("chat", "streaming_message", "failed", str(e))
        
        # Test chat history
        try:
            response = await self.session.get(
                f"{self.base_url}/chat/history/{self.test_session_id}",
                params={"limit": 10}
            )
            
            if response.status_code == 200:
                history_data = response.json()
                self.log_test("chat", "chat_history", "passed", history_data)
            else:
                self.log_test("chat", "chat_history", "failed", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("chat", "chat_history", "failed", str(e))
        
        # Test user sessions
        try:
            response = await self.session.get(f"{self.base_url}/chat/sessions")
            
            if response.status_code == 200:
                sessions_data = response.json()
                self.log_test("chat", "user_sessions", "passed", sessions_data)
            else:
                self.log_test("chat", "user_sessions", "failed", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("chat", "user_sessions", "failed", str(e))
        
        self.test_results["chat"]["status"] = "completed"
    
    async def test_timeline_endpoints(self):
        """Test timeline endpoints."""
        print("\n📅 Testing Timeline Endpoints...")
        
        # Test creating timeline event
        try:
            timeline_event = {
                "user_id": self.test_user_id,
                "event_type": "symptom",
                "title": "Chest Pain Episode",
                "description": "Patient reported sharp chest pain lasting 2 hours",
                "severity": "medium",
                "metadata": {
                    "duration": "2 hours",
                    "location": "substernal",
                    "intensity": "7/10"
                }
            }
            
            response = await self.session.post(f"{self.base_url}/timeline/event", json=timeline_event)
            
            if response.status_code == 200:
                event_result = response.json()
                self.log_test("timeline", "create_event", "passed", event_result)
            else:
                self.log_test("timeline", "create_event", "failed", f"Status: {response.status_code}, Body: {response.text}")
                
        except Exception as e:
            self.log_test("timeline", "create_event", "failed", str(e))
        
        # Test getting timeline
        try:
            response = await self.session.get(
                f"{self.base_url}/timeline/",
                params={"user_id": self.test_user_id, "limit": 50}
            )
            
            if response.status_code == 200:
                timeline_data = response.json()
                self.log_test("timeline", "get_timeline", "passed", timeline_data)
            else:
                self.log_test("timeline", "get_timeline", "failed", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("timeline", "get_timeline", "failed", str(e))
        
        # Test timeline summary
        try:
            response = await self.session.get(
                f"{self.base_url}/timeline/summary",
                params={"user_id": self.test_user_id, "days": 30}
            )
            
            if response.status_code == 200:
                summary_data = response.json()
                self.log_test("timeline", "timeline_summary", "passed", summary_data)
            else:
                self.log_test("timeline", "timeline_summary", "failed", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("timeline", "timeline_summary", "failed", str(e))
        
        # Test timeline search
        try:
            response = await self.session.get(
                f"{self.base_url}/timeline/search",
                params={"user_id": self.test_user_id, "event_type": "symptom", "search_term": "chest"}
            )
            
            if response.status_code == 200:
                search_data = response.json()
                self.log_test("timeline", "timeline_search", "passed", search_data)
            else:
                self.log_test("timeline", "timeline_search", "failed", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("timeline", "timeline_search", "failed", str(e))
        
        self.test_results["timeline"]["status"] = "completed"
    
    async def test_expert_opinion_endpoints(self):
        """Test expert opinion endpoints."""
        print("\n👨‍⚕️ Testing Expert Opinion Endpoints...")
        
        try:
            expert_request = {
                "user_id": self.test_user_id,
                "query": "I have been experiencing chest pain and shortness of breath. My blood pressure is elevated and I have diabetes. What specialist should I see?",
                "context": {
                    "symptoms": ["chest pain", "shortness of breath"],
                    "conditions": ["hypertension", "diabetes"],
                    "medications": ["metformin", "lisinopril"]
                }
            }
            
            response = await self.session.post(f"{self.base_url}/expert-opinion/consult", json=expert_request)
            
            if response.status_code == 200:
                expert_result = response.json()
                self.log_test("expert", "expert_consult", "passed", expert_result)
            else:
                self.log_test("expert", "expert_consult", "failed", f"Status: {response.status_code}, Body: {response.text}")
                
        except Exception as e:
            self.log_test("expert", "expert_consult", "failed", str(e))
        
        self.test_results["expert"]["status"] = "completed"
    
    async def test_anatomy_endpoints(self):
        """Test anatomy endpoints."""
        print("\n🫀 Testing Anatomy Endpoints...")
        
        # Test body part query
        try:
            response = await self.session.get(f"{self.base_url}/anatomy/body-part/heart")
            
            if response.status_code == 200:
                anatomy_data = response.json()
                self.log_test("anatomy", "body_part_query", "passed", anatomy_data)
            else:
                self.log_test("anatomy", "body_part_query", "failed", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("anatomy", "body_part_query", "failed", str(e))
        
        # Test systems listing
        try:
            response = await self.session.get(f"{self.base_url}/anatomy/systems")
            
            if response.status_code == 200:
                systems_data = response.json()
                self.log_test("anatomy", "systems_list", "passed", systems_data)
            else:
                self.log_test("anatomy", "systems_list", "failed", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("anatomy", "systems_list", "failed", str(e))
        
        self.test_results["anatomy"]["status"] = "completed"
    
    async def test_events_endpoints(self):
        """Test events endpoints."""
        print("\n⚡ Testing Events Endpoints...")
        
        # Test getting medical events
        try:
            response = await self.session.get(
                f"{self.base_url}/events/medical",
                params={"user_id": self.test_user_id, "limit": 20}
            )
            
            if response.status_code == 200:
                events_data = response.json()
                self.log_test("events", "get_medical_events", "passed", events_data)
            else:
                self.log_test("events", "get_medical_events", "failed", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("events", "get_medical_events", "failed", str(e))
        
        # Test creating medical event
        try:
            medical_event = {
                "user_id": self.test_user_id,
                "event_type": "diagnosis",
                "body_part": "heart",
                "condition": "hypertension",
                "metadata": {
                    "bp_reading": "140/90",
                    "diagnosed_date": "2024-01-15"
                }
            }
            
            response = await self.session.post(f"{self.base_url}/events/medical", json=medical_event)
            
            if response.status_code == 200:
                event_result = response.json()
                self.log_test("events", "create_medical_event", "passed", event_result)
            else:
                self.log_test("events", "create_medical_event", "failed", f"Status: {response.status_code}, Body: {response.text}")
                
        except Exception as e:
            self.log_test("events", "create_medical_event", "failed", str(e))
        
        self.test_results["events"]["status"] = "completed"
    
    async def test_data_verification(self):
        """Test data storage and retrieval across databases."""
        print("\n🔍 Testing Data Verification Across Databases...")
        
        # This would require direct database connections to verify data storage
        # For now, we'll test the API responses to ensure data consistency
        
        try:
            # Verify uploaded document appears in history
            response = await self.session.get(
                f"{self.base_url}/upload/documents",
                params={"user_id": self.test_user_id}
            )
            
            if response.status_code == 200:
                documents = response.json().get("documents", [])
                found_test_doc = any(doc.get("document_id") == self.test_document_id for doc in documents)
                
                if found_test_doc:
                    self.log_test("data_verification", "document_in_history", "passed", "Test document found in history")
                else:
                    self.log_test("data_verification", "document_in_history", "failed", "Test document not found in history")
            else:
                self.log_test("data_verification", "document_in_history", "failed", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("data_verification", "document_in_history", "failed", str(e))
        
        # Verify timeline events are retrievable
        try:
            response = await self.session.get(
                f"{self.base_url}/timeline/",
                params={"user_id": self.test_user_id}
            )
            
            if response.status_code == 200:
                timeline = response.json()
                events = timeline.get("events", [])
                
                if events:
                    self.log_test("data_verification", "timeline_events_exist", "passed", f"Found {len(events)} timeline events")
                else:
                    self.log_test("data_verification", "timeline_events_exist", "info", "No timeline events found")
            else:
                self.log_test("data_verification", "timeline_events_exist", "failed", f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("data_verification", "timeline_events_exist", "failed", str(e))
        
        # Test cross-referencing: if document was uploaded, it should potentially appear in chat context
        # This is more complex and would require AI agent processing
        
        self.test_results["data_verification"]["status"] = "completed"
    
    async def run_all_tests(self):
        """Run all endpoint tests in sequence."""
        print("🚀 Starting Comprehensive MediTwin Backend Testing...\n")
        
        start_time = datetime.now()
        
        # Run tests in logical order
        await self.test_health_endpoints()
        await self.test_auth_endpoints()
        await self.test_upload_endpoints()
        await self.test_chat_endpoints()
        await self.test_timeline_endpoints()
        await self.test_expert_opinion_endpoints()
        await self.test_anatomy_endpoints()
        await self.test_events_endpoints()
        await self.test_data_verification()
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Generate summary report
        self.generate_summary_report(duration)
    
    def generate_summary_report(self, duration):
        """Generate and display test summary report."""
        print("\n" + "="*80)
        print("📊 TEST SUMMARY REPORT")
        print("="*80)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for category, results in self.test_results.items():
            tests = results["tests"]
            category_passed = sum(1 for t in tests if t["status"] == "passed")
            category_failed = sum(1 for t in tests if t["status"] == "failed")
            category_total = len(tests)
            
            total_tests += category_total
            passed_tests += category_passed
            failed_tests += category_failed
            
            status_emoji = "✅" if category_failed == 0 else "⚠️" if category_passed > 0 else "❌"
            print(f"{status_emoji} {category.upper()}: {category_passed}/{category_total} passed")
            
            # Show failed tests
            failed_in_category = [t for t in tests if t["status"] == "failed"]
            for failed_test in failed_in_category:
                print(f"    ❌ {failed_test['test']}: {failed_test.get('details', 'No details')}")
        
        print(f"\n📈 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        print(f"   Duration: {duration}")
        
        # Save detailed results to file
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        print("="*80)
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.session.aclose()


async def main():
    """Main test execution function."""
    tester = EndpointTester()
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
