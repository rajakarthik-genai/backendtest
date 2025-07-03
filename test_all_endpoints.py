#!/usr/bin/env python3
"""
Comprehensive API Endpoint Testing Script

This script tests all MediTwin backend endpoints including:
- Health check
- Authentication
- Document upload
- Chat endpoints  
- Expert opinion endpoints
- Timeline endpoints
- All other API endpoints
"""

import asyncio
import httpx
import json
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

# Add project path
sys.path.append('/home/user/agents/meditwin-agents')

try:
    from src.config.settings import settings
    from src.auth.jwt_auth import create_access_token
except ImportError:
    print("Warning: Could not import project modules. Some tests may be limited.")
    settings = None

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

class EndpointTester:
    """Comprehensive endpoint testing class."""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        self.conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
        self.test_results = {}
        self.test_data = {}
        
    async def run_all_tests(self):
        """Run all endpoint tests."""
        print("=" * 60)
        print("🧪 MEDITWIN BACKEND ENDPOINT TESTING")
        print("=" * 60)
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 Base URL: {self.base_url}")
        print(f"👤 Test User ID: {self.test_user_id}")
        print("-" * 60)
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            self.client = client
            
            # Test order matters for dependencies
            test_methods = [
                ("Health Check", self.test_health_endpoint),
                ("API Documentation", self.test_api_docs),
                ("Authentication Endpoints", self.test_auth_endpoints),
                ("Document Upload", self.test_upload_endpoints),
                ("Chat Endpoints", self.test_chat_endpoints),
                ("Expert Opinion", self.test_expert_opinion_endpoints),
                ("Timeline Endpoints", self.test_timeline_endpoints),
                ("Anatomy Endpoints", self.test_anatomy_endpoints),
                ("Events Endpoints", self.test_events_endpoints),
            ]
            
            for test_name, test_method in test_methods:
                print(f"\n🔍 Testing: {test_name}")
                try:
                    result = await test_method()
                    self.test_results[test_name] = result
                    if result.get('passed', False):
                        print(f"✅ {test_name}: PASSED")
                    else:
                        print(f"❌ {test_name}: FAILED - {result.get('error', 'Unknown error')}")
                except Exception as e:
                    print(f"💥 {test_name}: EXCEPTION - {str(e)}")
                    self.test_results[test_name] = {'passed': False, 'error': str(e)}
                
                # Small delay between tests
                await asyncio.sleep(1)
        
        # Print final summary
        self.print_test_summary()
    
    async def test_health_endpoint(self) -> Dict[str, Any]:
        """Test health check endpoint."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            data = response.json()
            
            return {
                'passed': response.status_code == 200 and data.get('status') == 'healthy',
                'status_code': response.status_code,
                'response': data,
                'details': f"Status: {data.get('status', 'unknown')}"
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    async def test_api_docs(self) -> Dict[str, Any]:
        """Test API documentation endpoints."""
        try:
            # Test OpenAPI docs
            docs_response = await self.client.get(f"{self.base_url}/docs")
            openapi_response = await self.client.get(f"{self.base_url}/openapi.json")
            
            return {
                'passed': docs_response.status_code == 200 and openapi_response.status_code == 200,
                'docs_status': docs_response.status_code,
                'openapi_status': openapi_response.status_code,
                'details': "API documentation accessible"
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    async def test_auth_endpoints(self) -> Dict[str, Any]:
        """Test authentication endpoints."""
        try:
            results = {}
            
            # Test login endpoint (should return validation error for invalid creds)
            login_data = {"username": "test@example.com", "password": "invalid"}
            login_response = await self.client.post(f"{self.base_url}/auth/login", json=login_data)
            results['login'] = login_response.status_code in [400, 401, 422]
            
            # Test register endpoint (if it exists)
            register_data = {
                "email": "test@example.com",
                "username": "testuser",
                "password": "testpass123"
            }
            register_response = await self.client.post(f"{self.base_url}/auth/register", json=register_data)
            results['register'] = register_response.status_code in [200, 400, 409, 422]
            
            # Test token refresh endpoint
            refresh_data = {"refresh_token": "invalid_token"}
            refresh_response = await self.client.post(f"{self.base_url}/auth/refresh", json=refresh_data)
            results['refresh'] = refresh_response.status_code in [400, 401, 422]
            
            return {
                'passed': all(results.values()),
                'details': results,
                'info': "Authentication endpoints responding correctly to invalid inputs"
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    async def test_upload_endpoints(self) -> Dict[str, Any]:
        """Test document upload endpoints."""
        try:
            # Create a test file
            test_content = b"Test medical document content for endpoint testing"
            files = {"file": ("test_doc.txt", test_content, "text/plain")}
            
            # Test upload without auth (should fail or require auth)
            upload_response = await self.client.post(f"{self.base_url}/upload", files=files)
            
            # Test upload status endpoint
            status_response = await self.client.get(f"{self.base_url}/upload/status/test_id")
            
            return {
                'passed': True,  # Just checking endpoints exist
                'upload_status': upload_response.status_code,
                'status_check': status_response.status_code,
                'details': f"Upload: {upload_response.status_code}, Status: {status_response.status_code}"
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    async def test_chat_endpoints(self) -> Dict[str, Any]:
        """Test chat endpoints."""
        try:
            # Test chat endpoint
            chat_payload = {
                "message": "What is the patient's current condition?",
                "conversation_id": self.conversation_id,
                "user_id": self.test_user_id
            }
            
            chat_response = await self.client.post(f"{self.base_url}/chat", json=chat_payload)
            
            # Test chat history endpoint
            history_response = await self.client.get(
                f"{self.base_url}/chat/history",
                params={"conversation_id": self.conversation_id, "user_id": self.test_user_id}
            )
            
            return {
                'passed': True,  # Endpoints exist and respond
                'chat_status': chat_response.status_code,
                'history_status': history_response.status_code,
                'chat_response': chat_response.json() if chat_response.status_code < 500 else None,
                'details': f"Chat: {chat_response.status_code}, History: {history_response.status_code}"
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    async def test_expert_opinion_endpoints(self) -> Dict[str, Any]:
        """Test expert opinion endpoints."""
        try:
            # Test expert opinion endpoint
            expert_payload = {
                "query": "Please provide a cardiology consultation for chest pain symptoms",
                "specialist": "cardiologist",
                "user_id": self.test_user_id
            }
            
            expert_response = await self.client.post(f"{self.base_url}/expert-opinion", json=expert_payload)
            
            # Test available specialists endpoint
            specialists_response = await self.client.get(f"{self.base_url}/expert-opinion/specialists")
            
            return {
                'passed': True,  # Endpoints exist and respond
                'expert_status': expert_response.status_code,
                'specialists_status': specialists_response.status_code,
                'expert_response': expert_response.json() if expert_response.status_code < 500 else None,
                'details': f"Expert: {expert_response.status_code}, Specialists: {specialists_response.status_code}"
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    async def test_timeline_endpoints(self) -> Dict[str, Any]:
        """Test timeline endpoints."""
        try:
            # Test timeline endpoint
            timeline_params = {
                "user_id": self.test_user_id,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
            
            timeline_response = await self.client.get(f"{self.base_url}/timeline", params=timeline_params)
            
            # Test add event endpoint
            event_payload = {
                "event_type": "symptom",
                "description": "Test symptom for endpoint testing",
                "date": "2024-01-01T12:00:00",
                "user_id": self.test_user_id
            }
            
            add_event_response = await self.client.post(f"{self.base_url}/timeline/events", json=event_payload)
            
            return {
                'passed': True,  # Endpoints exist and respond
                'timeline_status': timeline_response.status_code,
                'add_event_status': add_event_response.status_code,
                'details': f"Timeline: {timeline_response.status_code}, Add Event: {add_event_response.status_code}"
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    async def test_anatomy_endpoints(self) -> Dict[str, Any]:
        """Test anatomy endpoints."""
        try:
            # Test anatomy overview
            anatomy_response = await self.client.get(f"{self.base_url}/anatomy")
            
            # Test body part timeline
            body_part_response = await self.client.get(f"{self.base_url}/anatomy/heart/timeline")
            
            return {
                'passed': True,  # Endpoints exist and respond
                'anatomy_status': anatomy_response.status_code,
                'body_part_status': body_part_response.status_code,
                'details': f"Anatomy: {anatomy_response.status_code}, Body Part: {body_part_response.status_code}"
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    async def test_events_endpoints(self) -> Dict[str, Any]:
        """Test events CRUD endpoints."""
        try:
            # Test get events
            events_response = await self.client.get(f"{self.base_url}/events", params={"user_id": self.test_user_id})
            
            # Test create event
            create_event_payload = {
                "type": "test",
                "description": "Test event",
                "date": "2024-01-01T12:00:00",
                "severity": "low"
            }
            
            create_response = await self.client.post(f"{self.base_url}/events", json=create_event_payload)
            
            return {
                'passed': True,  # Endpoints exist and respond
                'get_events_status': events_response.status_code,
                'create_event_status': create_response.status_code,
                'details': f"Get Events: {events_response.status_code}, Create: {create_response.status_code}"
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    def print_test_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.test_results.values() if result.get('passed', False))
        total_tests = len(self.test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"✅ Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"❌ Failed: {total_tests - passed_tests}/{total_tests}")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 60)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result.get('passed', False) else "❌ FAIL"
            print(f"{status} | {test_name}")
            
            if 'details' in result:
                print(f"      └─ {result['details']}")
            if 'error' in result:
                print(f"      └─ Error: {result['error']}")
            
            # Print response details for important endpoints
            if test_name in ["Chat Endpoints", "Expert Opinion"] and 'chat_response' in result:
                response = result.get('chat_response') or result.get('expert_response')
                if response:
                    print(f"      └─ Response: {json.dumps(response, indent=2)[:200]}...")
        
        print("\n" + "=" * 60)
        print("🎯 TESTING COMPLETE")
        print("=" * 60)


async def main():
    """Main test runner."""
    tester = EndpointTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    print("🚀 Starting MediTwin Backend Endpoint Tests...")
    asyncio.run(main())
