#!/usr/bin/env python3
"""
Test script to verify the document processing implementation.

This script tests the core functionality implemented in the documents endpoint
based on the comprehensive audit requirements.
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime
from typing import Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentTestSuite:
    """Test suite for document processing functionality."""
    
    def __init__(self):
        self.test_results = {}
        self.passed_tests = 0
        self.total_tests = 0
    
    def log_test_result(self, test_name: str, passed: bool, message: str = "", details: Dict = None):
        """Log test result."""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
        
        self.test_results[test_name] = {
            "passed": passed,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        status = "PASS" if passed else "FAIL"
        logger.info(f"[{status}] {test_name}: {message}")
    
    async def test_import_dependencies(self):
        """Test that all required dependencies can be imported."""
        try:
            # Test core imports
            from src.api.v1.endpoints.documents import router
            from src.agents.crew_agents.medical_crew import MedicalDocumentCrew, process_medical_document
            from src.db.redis_db import get_redis
            from src.db.mongo_db import get_mongo
            from src.db.neo4j_db import get_neo4j
            from src.db.milvus_db import get_milvus
            from src.auth.dependencies import CurrentUser
            
            self.log_test_result(
                "import_dependencies", 
                True, 
                "All required dependencies imported successfully"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "import_dependencies", 
                False, 
                f"Failed to import dependencies: {str(e)}"
            )
            return False
    
    async def test_crew_ai_initialization(self):
        """Test that CrewAI system can be initialized."""
        try:
            from src.agents.crew_agents.medical_crew import MedicalDocumentCrew
            
            crew = MedicalDocumentCrew()
            
            # Check that all agents are initialized
            agents_present = [
                hasattr(crew, 'document_reader'),
                hasattr(crew, 'clinical_extractor'),
                hasattr(crew, 'vector_embedder'),
                hasattr(crew, 'storage_coordinator')
            ]
            
            if all(agents_present):
                self.log_test_result(
                    "crew_ai_initialization", 
                    True, 
                    "CrewAI medical document crew initialized successfully",
                    {"agents_count": len(crew.crew.agents)}
                )
                return True
            else:
                self.log_test_result(
                    "crew_ai_initialization", 
                    False, 
                    "Not all agents are present in crew",
                    {"agents_present": agents_present}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "crew_ai_initialization", 
                False, 
                f"CrewAI initialization failed: {str(e)}"
            )
            return False
    
    async def test_database_connections(self):
        """Test database connection initialization."""
        db_results = {}
        
        # Test Redis
        try:
            from src.db.redis_db import get_redis
            redis_client = await get_redis()
            db_results["redis"] = {"available": True, "error": None}
        except Exception as e:
            db_results["redis"] = {"available": False, "error": str(e)}
        
        # Test MongoDB
        try:
            from src.db.mongo_db import get_mongo
            mongo_client = await get_mongo()
            db_results["mongodb"] = {"available": True, "error": None}
        except Exception as e:
            db_results["mongodb"] = {"available": False, "error": str(e)}
        
        # Test Neo4j
        try:
            from src.db.neo4j_db import get_neo4j
            neo4j_client = await get_neo4j()
            db_results["neo4j"] = {"available": True, "error": None}
        except Exception as e:
            db_results["neo4j"] = {"available": False, "error": str(e)}
        
        # Test Milvus
        try:
            from src.db.milvus_db import get_milvus
            milvus_client = await get_milvus()
            db_results["milvus"] = {"available": True, "error": None}
        except Exception as e:
            db_results["milvus"] = {"available": False, "error": str(e)}
        
        available_dbs = sum(1 for db in db_results.values() if db["available"])
        total_dbs = len(db_results)
        
        self.log_test_result(
            "database_connections",
            available_dbs > 0,
            f"{available_dbs}/{total_dbs} databases available",
            db_results
        )
        
        return available_dbs > 0
    
    async def test_redis_status_functionality(self):
        """Test Redis processing status functionality."""
        try:
            from src.db.redis_db import get_redis
            
            redis_client = await get_redis()
            
            # Test storing status
            test_doc_id = "test_doc_12345"
            test_status = "processing"
            test_metadata = {
                "patient_id": "test_patient",
                "filename": "test.pdf",
                "file_size": 1024
            }
            
            # Store status
            store_result = await redis_client.store_processing_status(
                test_doc_id, test_status, test_metadata
            )
            
            if not store_result:
                raise Exception("Failed to store processing status")
            
            # Retrieve status
            retrieved_status = await redis_client.get_processing_status(test_doc_id)
            
            if not retrieved_status:
                raise Exception("Failed to retrieve processing status")
            
            # Validate status
            if (retrieved_status.get("status") == test_status and 
                retrieved_status.get("metadata", {}).get("patient_id") == "test_patient"):
                
                self.log_test_result(
                    "redis_status_functionality",
                    True,
                    "Redis status storage and retrieval working correctly"
                )
                return True
            else:
                raise Exception("Retrieved status does not match stored status")
                
        except Exception as e:
            self.log_test_result(
                "redis_status_functionality",
                False,
                f"Redis status functionality failed: {str(e)}"
            )
            return False
    
    async def test_rate_limiting(self):
        """Test upload rate limiting functionality."""
        try:
            # Import the rate limiting function from the documents module
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            
            from src.api.v1.endpoints.documents import check_upload_rate_limit
            
            test_patient_id = "test_patient_rate_limit"
            
            # Test that first upload is allowed
            first_upload = check_upload_rate_limit(test_patient_id, max_uploads=2, time_window=60)
            
            if not first_upload:
                raise Exception("First upload should be allowed")
            
            # Test that second upload is allowed
            second_upload = check_upload_rate_limit(test_patient_id, max_uploads=2, time_window=60)
            
            if not second_upload:
                raise Exception("Second upload should be allowed")
            
            # Test that third upload is blocked
            third_upload = check_upload_rate_limit(test_patient_id, max_uploads=2, time_window=60)
            
            if third_upload:
                raise Exception("Third upload should be blocked")
            
            self.log_test_result(
                "rate_limiting",
                True,
                "Rate limiting functionality working correctly"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "rate_limiting",
                False,
                f"Rate limiting test failed: {str(e)}"
            )
            return False
    
    async def test_document_validation_models(self):
        """Test document validation models."""
        try:
            from src.api.v1.endpoints.documents import DocumentValidationError, DocumentValidationResponse
            
            # Test validation error model
            error = DocumentValidationError(
                field="test_field",
                message="Test error message",
                code="TEST_ERROR"
            )
            
            # Test validation response model
            response = DocumentValidationResponse(
                valid=False,
                errors=[error],
                warnings=["Test warning"],
                file_info={"filename": "test.pdf", "size_bytes": 1024}
            )
            
            # Validate that models can be serialized
            error_dict = error.model_dump()
            response_dict = response.model_dump()
            
            if (error_dict["field"] == "test_field" and 
                response_dict["valid"] == False and
                len(response_dict["errors"]) == 1):
                
                self.log_test_result(
                    "document_validation_models",
                    True,
                    "Document validation models working correctly"
                )
                return True
            else:
                raise Exception("Model validation failed")
                
        except Exception as e:
            self.log_test_result(
                "document_validation_models",
                False,
                f"Document validation models test failed: {str(e)}"
            )
            return False
    
    async def test_background_task_function(self):
        """Test that background processing function is properly defined."""
        try:
            from src.api.v1.endpoints.documents import process_document_background
            import inspect
            
            # Check function signature
            sig = inspect.signature(process_document_background)
            expected_params = ['patient_id', 'document_id', 'file_path', 'metadata']
            actual_params = list(sig.parameters.keys())
            
            if actual_params != expected_params:
                raise Exception(f"Function signature mismatch. Expected: {expected_params}, Got: {actual_params}")
            
            # Check that function is async
            if not inspect.iscoroutinefunction(process_document_background):
                raise Exception("process_document_background should be an async function")
            
            self.log_test_result(
                "background_task_function",
                True,
                "Background task function properly defined"
            )
            return True
            
        except Exception as e:
            self.log_test_result(
                "background_task_function",
                False,
                f"Background task function test failed: {str(e)}"
            )
            return False
    
    async def test_endpoint_definitions(self):
        """Test that all expected endpoints are defined."""
        try:
            from src.api.v1.endpoints.documents import router
            
            # Get all routes from the router
            routes = [route.path for route in router.routes]
            
            expected_endpoints = [
                "/upload",
                "/batch-upload", 
                "/process/{document_id}",
                "/status/{document_id}",
                "/process-sync",
                "/list",
                "/detail/{document_id}",
                "/documents",
                "/documents/search",
                "/documents/insights", 
                "/documents/analyze",
                "/validate",
                "/stats",
                "/health",
                "/document/{document_id}"  # DELETE endpoint
            ]
            
            missing_endpoints = []
            for endpoint in expected_endpoints:
                # Check if endpoint pattern exists (accounting for FastAPI route matching)
                found = False
                for route in routes:
                    if endpoint.replace("{", "").replace("}", "") in route.replace("{", "").replace("}", ""):
                        found = True
                        break
                if not found:
                    missing_endpoints.append(endpoint)
            
            if not missing_endpoints:
                self.log_test_result(
                    "endpoint_definitions",
                    True,
                    f"All {len(expected_endpoints)} expected endpoints are defined",
                    {"defined_endpoints": routes}
                )
                return True
            else:
                self.log_test_result(
                    "endpoint_definitions",
                    False,
                    f"Missing endpoints: {missing_endpoints}",
                    {"missing": missing_endpoints, "defined": routes}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "endpoint_definitions",
                False,
                f"Endpoint definitions test failed: {str(e)}"
            )
            return False
    
    async def run_all_tests(self):
        """Run all tests and return summary."""
        logger.info("Starting document processing implementation test suite...")
        
        # Run all tests
        tests = [
            self.test_import_dependencies,
            self.test_crew_ai_initialization,
            self.test_database_connections,
            self.test_redis_status_functionality,
            self.test_rate_limiting,
            self.test_document_validation_models,
            self.test_background_task_function,
            self.test_endpoint_definitions
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                logger.error(f"Test {test.__name__} crashed: {e}")
                self.log_test_result(
                    test.__name__,
                    False,
                    f"Test crashed: {str(e)}"
                )
        
        # Generate summary
        summary = {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.total_tests - self.passed_tests,
            "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
            "test_results": self.test_results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Test suite completed: {self.passed_tests}/{self.total_tests} tests passed ({summary['success_rate']:.1f}%)")
        
        return summary


async def main():
    """Run the test suite."""
    test_suite = DocumentTestSuite()
    summary = await test_suite.run_all_tests()
    
    # Save results to file
    with open("document_implementation_test_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "="*50)
    print("DOCUMENT PROCESSING IMPLEMENTATION TEST RESULTS")
    print("="*50)
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['success_rate']:.1f}%")
    print("\nDetailed results saved to: document_implementation_test_results.json")
    
    if summary['failed_tests'] > 0:
        print("\nFAILED TESTS:")
        for test_name, result in summary['test_results'].items():
            if not result['passed']:
                print(f"  - {test_name}: {result['message']}")
    
    return summary['success_rate'] == 100.0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
