"""
Health Check Testing Module

This module contains comprehensive health checks for all system components
including databases, APIs, memory systems, and security validations.
"""

import asyncio
import pytest
import sys
from typing import Dict, Any, List
from datetime import datetime
import json

# Add project root to path
sys.path.append('/home/user/agents/meditwin-agents')

from src.db.mongodb import get_database
from src.db.neo4j import neo4j_connection
from src.db.redis_db import get_redis
from src.db.milvus_client import get_milvus_client
from src.chat.short_term import get_short_term_memory
from src.utils.logging import logger


class HealthCheckTestSuite:
    """Comprehensive health check test suite for all system components"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "UNKNOWN",
            "components": {},
            "security_checks": {},
            "performance_metrics": {}
        }
    
    async def test_database_connections(self) -> Dict[str, Any]:
        """Test all database connections"""
        results = {}
        
        # MongoDB Health Check
        try:
            mongo_db = await get_database()
            if mongo_db:
                # Test basic operation
                await mongo_db.list_collection_names()
                results["mongodb"] = {"status": "HEALTHY", "error": None}
            else:
                results["mongodb"] = {"status": "UNHEALTHY", "error": "Connection failed"}
        except Exception as e:
            results["mongodb"] = {"status": "UNHEALTHY", "error": str(e)}
        
        # Neo4j Health Check
        try:
            neo4j_connection._connect()
            if neo4j_connection.driver:
                # Test basic query
                test_result = neo4j_connection.execute_query("RETURN 1 as test")
                if test_result:
                    results["neo4j"] = {"status": "HEALTHY", "error": None}
                else:
                    results["neo4j"] = {"status": "UNHEALTHY", "error": "Query failed"}
            else:
                results["neo4j"] = {"status": "UNHEALTHY", "error": "Driver not initialized"}
        except Exception as e:
            results["neo4j"] = {"status": "UNHEALTHY", "error": str(e)}
        
        # Redis Health Check
        try:
            redis_client = get_redis()
            if redis_client and hasattr(redis_client, 'client'):
                # Test ping
                redis_client.client.ping()
                results["redis"] = {"status": "HEALTHY", "error": None}
            else:
                results["redis"] = {"status": "UNHEALTHY", "error": "Client not initialized"}
        except Exception as e:
            results["redis"] = {"status": "UNHEALTHY", "error": str(e)}
        
        # Milvus Health Check
        try:
            milvus_client = get_milvus_client()
            if milvus_client:
                # Test connection
                collections = milvus_client.list_collections()
                results["milvus"] = {"status": "HEALTHY", "error": None, "collections": len(collections)}
            else:
                results["milvus"] = {"status": "UNHEALTHY", "error": "Client not initialized"}
        except Exception as e:
            results["milvus"] = {"status": "UNHEALTHY", "error": str(e)}
        
        return results
    
    async def test_memory_systems(self) -> Dict[str, Any]:
        """Test memory system functionality"""
        results = {}
        
        try:
            # Test ShortTermMemory
            stm = get_short_term_memory()
            if stm:
                # Test that required methods exist
                required_methods = ['get_recent_messages', 'store_message', 'get_context']
                missing_methods = [method for method in required_methods 
                                 if not hasattr(stm, method)]
                
                if not missing_methods:
                    results["short_term_memory"] = {
                        "status": "HEALTHY", 
                        "error": None,
                        "methods_available": required_methods
                    }
                else:
                    results["short_term_memory"] = {
                        "status": "UNHEALTHY", 
                        "error": f"Missing methods: {missing_methods}"
                    }
            else:
                results["short_term_memory"] = {"status": "UNHEALTHY", "error": "STM not initialized"}
                
        except Exception as e:
            results["short_term_memory"] = {"status": "UNHEALTHY", "error": str(e)}
        
        return results
    
    async def test_hipaa_compliance(self) -> Dict[str, Any]:
        """Test HIPAA compliance and security measures"""
        results = {}
        
        try:
            # Test patient isolation validation exists
            if hasattr(neo4j_connection, 'validate_patient_isolation'):
                results["patient_isolation_validation"] = {"status": "HEALTHY", "error": None}
            else:
                results["patient_isolation_validation"] = {
                    "status": "UNHEALTHY", 
                    "error": "Patient isolation validation not implemented"
                }
            
            # Test data fix methods exist
            if hasattr(neo4j_connection, 'fix_patient_data_isolation'):
                results["patient_data_fix"] = {"status": "HEALTHY", "error": None}
            else:
                results["patient_data_fix"] = {
                    "status": "UNHEALTHY", 
                    "error": "Patient data fix methods not implemented"
                }
            
            # Test event node creation includes patient_id
            import inspect
            sig = inspect.signature(neo4j_connection.create_event_node)
            if 'patient_id' in sig.parameters:
                results["event_node_isolation"] = {"status": "HEALTHY", "error": None}
            else:
                results["event_node_isolation"] = {
                    "status": "UNHEALTHY", 
                    "error": "Event nodes don't enforce patient isolation"
                }
                
        except Exception as e:
            results["hipaa_compliance"] = {"status": "UNHEALTHY", "error": str(e)}
        
        return results
    
    async def test_api_endpoints_health(self) -> Dict[str, Any]:
        """Test critical API endpoints availability"""
        results = {}
        
        try:
            # Import API modules to check they can be loaded
            from src.api.routers.chat import router as chat_router
            from src.api.routers.documents import router as documents_router
            from src.api.routers.auth import router as auth_router
            
            results["api_modules"] = {
                "chat_router": "LOADED",
                "documents_router": "LOADED", 
                "auth_router": "LOADED",
                "status": "HEALTHY"
            }
            
        except Exception as e:
            results["api_modules"] = {"status": "UNHEALTHY", "error": str(e)}
        
        return results
    
    async def test_agent_systems(self) -> Dict[str, Any]:
        """Test agent system availability"""
        results = {}
        
        try:
            # Test agent imports
            from src.agents.orchestrator_agent import OrchestratorAgent
            from src.agents.chat_agent import ChatAgent
            from src.agents.medical_agent import MedicalAgent
            from src.agents.ingestion_agent import IngestionAgent
            
            results["agent_imports"] = {
                "orchestrator": "LOADED",
                "chat": "LOADED",
                "medical": "LOADED", 
                "ingestion": "LOADED",
                "status": "HEALTHY"
            }
            
        except Exception as e:
            results["agent_imports"] = {"status": "UNHEALTHY", "error": str(e)}
        
        return results
    
    async def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive report"""
        print("🏥 Running Comprehensive Health Check...")
        print("=" * 50)
        
        # Database Health
        print("🔍 Testing Database Connections...")
        db_results = await self.test_database_connections()
        self.results["components"]["databases"] = db_results
        
        # Memory Systems Health
        print("🧠 Testing Memory Systems...")
        memory_results = await self.test_memory_systems()
        self.results["components"]["memory"] = memory_results
        
        # HIPAA Compliance Health
        print("🔒 Testing HIPAA Compliance...")
        hipaa_results = await self.test_hipaa_compliance()
        self.results["security_checks"]["hipaa"] = hipaa_results
        
        # API Health
        print("🌐 Testing API Systems...")
        api_results = await self.test_api_endpoints_health()
        self.results["components"]["api"] = api_results
        
        # Agent Systems Health
        print("🤖 Testing Agent Systems...")
        agent_results = await self.test_agent_systems()
        self.results["components"]["agents"] = agent_results
        
        # Calculate overall status
        all_components = []
        for category in self.results["components"].values():
            if isinstance(category, dict):
                for component in category.values():
                    if isinstance(component, dict) and "status" in component:
                        all_components.append(component["status"])
        
        for category in self.results["security_checks"].values():
            if isinstance(category, dict):
                for component in category.values():
                    if isinstance(component, dict) and "status" in component:
                        all_components.append(component["status"])
        
        if all(status == "HEALTHY" for status in all_components):
            self.results["overall_status"] = "HEALTHY"
        elif any(status == "HEALTHY" for status in all_components):
            self.results["overall_status"] = "DEGRADED"
        else:
            self.results["overall_status"] = "CRITICAL"
        
        return self.results
    
    def print_health_report(self):
        """Print a formatted health report"""
        print("\n" + "=" * 60)
        print("🏥 MEDITWIN SYSTEM HEALTH REPORT")
        print("=" * 60)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Overall Status: {self.results['overall_status']}")
        print()
        
        # Database Status
        print("📊 DATABASE SYSTEMS:")
        for db, status in self.results["components"].get("databases", {}).items():
            status_icon = "✅" if status["status"] == "HEALTHY" else "❌"
            print(f"   {status_icon} {db.upper()}: {status['status']}")
            if status.get("error"):
                print(f"      Error: {status['error']}")
        print()
        
        # Memory Systems
        print("🧠 MEMORY SYSTEMS:")
        for mem, status in self.results["components"].get("memory", {}).items():
            status_icon = "✅" if status["status"] == "HEALTHY" else "❌"
            print(f"   {status_icon} {mem}: {status['status']}")
            if status.get("error"):
                print(f"      Error: {status['error']}")
        print()
        
        # Security/HIPAA
        print("🔒 SECURITY & HIPAA COMPLIANCE:")
        for sec, status in self.results["security_checks"].get("hipaa", {}).items():
            status_icon = "✅" if status["status"] == "HEALTHY" else "❌"
            print(f"   {status_icon} {sec}: {status['status']}")
            if status.get("error"):
                print(f"      Error: {status['error']}")
        print()
        
        # API Systems
        print("🌐 API SYSTEMS:")
        api_status = self.results["components"].get("api", {}).get("api_modules", {})
        if api_status.get("status") == "HEALTHY":
            print("   ✅ All API modules loaded successfully")
        else:
            print(f"   ❌ API modules: {api_status.get('error', 'Unknown error')}")
        print()
        
        # Agent Systems
        print("🤖 AGENT SYSTEMS:")
        agent_status = self.results["components"].get("agents", {}).get("agent_imports", {})
        if agent_status.get("status") == "HEALTHY":
            print("   ✅ All agent modules loaded successfully")
        else:
            print(f"   ❌ Agent modules: {agent_status.get('error', 'Unknown error')}")
        print()
        
        print("=" * 60)


# Test runner functions for pytest compatibility
@pytest.mark.asyncio
async def test_system_health():
    """Pytest-compatible health check test"""
    health_checker = HealthCheckTestSuite()
    results = await health_checker.run_comprehensive_health_check()
    
    # Assert system is not in critical state
    assert results["overall_status"] != "CRITICAL", f"System health is critical: {results}"
    
    return results


async def main():
    """Main function for running health checks standalone"""
    health_checker = HealthCheckTestSuite()
    results = await health_checker.run_comprehensive_health_check()
    health_checker.print_health_report()
    
    # Save results to file
    with open("/home/user/agents/meditwin-agents/tests/health_check_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"📄 Detailed results saved to: tests/health_check_results.json")
    
    return results["overall_status"] != "CRITICAL"


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
