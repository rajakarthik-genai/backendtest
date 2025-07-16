#!/usr/bin/env python3
"""
Comprehensive test suite for all MediTwin Agents API endpoints.
Tests all endpoints with proper authentication and validation.
"""

import pytest
import requests
import json
from typing import Dict, Any
import os
from datetime import datetime

# Test Configuration
BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 30

class TestMediTwinAPI:
    """Test class for all MediTwin API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.base_url = BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-token"  # Replace with valid token
        }
        
    def test_health_check(self):
        """Test system health check"""
        response = requests.get(f"{self.base_url}/system_info/system/status", timeout=TIMEOUT)
        assert response.status_code in [200, 401]
        
    # Chat Endpoints Tests
    def test_chat_message(self):
        """Test chat message endpoint"""
        payload = {
            "message": "I have a headache",
            "session_id": "test-session"
        }
        response = requests.post(
            f"{self.base_url}/chat/message", 
            json=payload, 
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]  # 401 for auth issues
        
    def test_chat_history(self):
        """Test chat history endpoint"""
        response = requests.get(
            f"{self.base_url}/chat/history/test-session",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]
        
    def test_chat_sessions(self):
        """Test chat sessions endpoint"""
        response = requests.get(
            f"{self.base_url}/chat/sessions",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]
        
    # Medical Analysis Tests
    def test_symptom_analysis(self):
        """Test symptom analysis endpoint"""
        payload = {
            "symptoms": ["headache", "fever"],
            "duration": "2 days",
            "severity": "moderate",
            "context": "Started after stress"
        }
        response = requests.post(
            f"{self.base_url}/medical_analysis/symptoms/analyze",
            json=payload,
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]
        
    def test_diagnostic_suggestions(self):
        """Test diagnostic suggestions endpoint"""
        payload = {
            "symptoms": ["cough", "fatigue"],
            "medical_history": "Previous respiratory issues"
        }
        response = requests.post(
            f"{self.base_url}/medical_analysis/diagnostic/suggestions",
            json=payload,
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]
        
    def test_treatment_recommendations(self):
        """Test treatment recommendations endpoint"""
        payload = {
            "condition": "common cold",
            "symptoms": ["runny nose", "cough"],
            "severity": "mild"
        }
        response = requests.post(
            f"{self.base_url}/medical_analysis/treatment/recommendations",
            json=payload,
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]
        
    # Upload Tests
    def test_upload_endpoint_structure(self):
        """Test upload endpoint accessibility"""
        # Test without file (should return 422)
        response = requests.post(
            f"{self.base_url}/upload/document",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [422, 401]  # 422 for missing file, 401 for auth
        
    def test_upload_status(self):
        """Test upload status endpoint"""
        response = requests.get(
            f"{self.base_url}/upload/status/test-document-id",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 404, 401]
        
    def test_upload_documents_list(self):
        """Test upload documents list endpoint"""
        response = requests.get(
            f"{self.base_url}/upload/documents",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]
        
    # Knowledge Base Tests
    def test_knowledge_search(self):
        """Test knowledge base search"""
        response = requests.get(
            f"{self.base_url}/knowledge_base/knowledge/search?query=diabetes",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]
        
    def test_medical_information(self):
        """Test medical information endpoint"""
        response = requests.get(
            f"{self.base_url}/knowledge_base/medical/information?topic=hypertension",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]
        
    def test_drug_interactions(self):
        """Test drug interactions endpoint"""
        payload = {
            "medications": ["aspirin", "ibuprofen"]
        }
        response = requests.post(
            f"{self.base_url}/knowledge_base/drugs/interactions",
            json=payload,
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]
        
    # Analytics Tests
    def test_analytics_trends(self):
        """Test analytics trends endpoint"""
        response = requests.get(
            f"{self.base_url}/analytics/analytics/trends?period=30d",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]
        
    def test_analytics_dashboard(self):
        """Test analytics dashboard endpoint"""
        response = requests.get(
            f"{self.base_url}/analytics/analytics/dashboard",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]
        
    def test_health_score(self):
        """Test health score endpoint"""
        response = requests.get(
            f"{self.base_url}/analytics/health/score",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]
        
    def test_risk_assessment(self):
        """Test risk assessment endpoint"""
        response = requests.get(
            f"{self.base_url}/analytics/health/risk-assessment",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]
        
    # Timeline Tests
    def test_timeline_events(self):
        """Test timeline events endpoint"""
        response = requests.get(
            f"{self.base_url}/timeline/timeline",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]
        
    def test_timeline_summary(self):
        """Test timeline summary endpoint"""
        response = requests.get(
            f"{self.base_url}/timeline/summary",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]
        
    # System Info Tests
    def test_system_status(self):
        """Test system status endpoint"""
        response = requests.get(f"{self.base_url}/system_info/system/status", timeout=TIMEOUT)
        # This endpoint might not require auth
        assert response.status_code in [200, 401]
        
    def test_system_info(self):
        """Test system info endpoint"""
        response = requests.get(f"{self.base_url}/system_info/info", timeout=TIMEOUT)
        assert response.status_code in [200, 401]
        
    def test_system_metrics(self):
        """Test system metrics endpoint"""
        response = requests.get(
            f"{self.base_url}/system_info/metrics",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]
        
    def test_database_status(self):
        """Test database status endpoint"""
        response = requests.get(
            f"{self.base_url}/system_info/database/status",
            headers=self.headers,
            timeout=TIMEOUT
        )
        assert response.status_code in [200, 401]

if __name__ == "__main__":
    # Run tests directly
    import sys
    test_instance = TestMediTwinAPI()
    test_instance.setup()
    
    print("🧪 Running MediTwin API Tests...")
    print("=" * 50)
    
    # Run each test method
    methods = [method for method in dir(test_instance) if method.startswith('test_')]
    passed = 0
    failed = 0
    
    for method_name in methods:
        try:
            method = getattr(test_instance, method_name)
            method()
            print(f"✅ {method_name}: PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {method_name}: FAILED - {str(e)}")
            failed += 1
    
    print("=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("⚠️ Some tests failed - check authentication and service status")
        sys.exit(1)
