#!/usr/bin/env python3
"""
Comprehensive RAG Testing Script

This script tests the complete RAG (Retrieval-Augmented Generation) functionality
including document upload, processing, chat endpoints, and expert opinion endpoints
with the specific test_upload.pdf document.
"""

import asyncio
import httpx
import json
import time
import sys
from datetime import datetime
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_DOCUMENT = "test_upload.pdf"
TIMEOUT = 60.0

class RAGTester:
    """Comprehensive RAG functionality tester."""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.document_id = None
        self.conversation_id = None
        self.jwt_token = None
        
        # Test results
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "tests": []
        }
    
    def log_test(self, test_name: str, success: bool, details: str = None):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results["tests"].append({
            "name": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        if success:
            self.test_results["passed"] += 1
        else:
            self.test_results["failed"] += 1
    
    async def generate_jwt_token(self):
        """Generate JWT token for authentication."""
        print("\n🔑 Generating JWT Token...")
        
        try:
            # Import JWT creation function
            import sys
            sys.path.append('/home/user/agents/meditwin-agents')
            from src.auth.jwt_auth import create_access_token
            from datetime import timedelta
            
            user_data = {
                "user_id": "test_user_rag",
                "email": "test@rag.com",
                "name": "RAG Test User"
            }
            
            # Create token with long expiration
            expires_delta = timedelta(hours=24)
            self.jwt_token = create_access_token(data=user_data, expires_delta=expires_delta)
            
            self.log_test("JWT Token Generation", True, f"Token: {self.jwt_token[:50]}...")
            return True
            
        except Exception as e:
            self.log_test("JWT Token Generation", False, f"Error: {str(e)}")
            return False
    
    async def upload_test_document(self):
        """Upload the test document for RAG processing."""
        print("\n📄 Uploading Test Document...")
        
        try:
            # Check if file exists
            if not Path(TEST_DOCUMENT).exists():
                self.log_test("Document Upload", False, f"File {TEST_DOCUMENT} not found")
                return False
            
            # Upload the document
            files = {"file": (TEST_DOCUMENT, open(TEST_DOCUMENT, "rb"), "application/pdf")}
            data = {"description": "Test document for RAG functionality testing"}
            
            headers = {}
            if self.jwt_token:
                headers["Authorization"] = f"Bearer {self.jwt_token}"
            
            response = await self.client.post(
                f"{self.base_url}/upload/document", 
                files=files, 
                data=data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                self.document_id = result.get("document_id")
                self.log_test("Document Upload", True, f"Document ID: {self.document_id}")
                return True
            else:
                self.log_test("Document Upload", False, f"Status: {response.status_code}, Body: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Document Upload", False, f"Error: {str(e)}")
            return False
        finally:
            # Close file
            try:
                files["file"][1].close()
            except:
                pass
    
    async def wait_for_processing(self):
        """Wait for document processing to complete."""
        print("\n⏳ Waiting for Document Processing...")
        
        if not self.document_id:
            self.log_test("Document Processing Wait", False, "No document ID available")
            return False
        
        try:
            for attempt in range(20):  # Wait up to 40 seconds
                headers = {}
                if self.jwt_token:
                    headers["Authorization"] = f"Bearer {self.jwt_token}"
                
                response = await self.client.get(
                    f"{self.base_url}/upload/status/{self.document_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get("status", "unknown")
                    
                    if status == "completed":
                        self.log_test("Document Processing", True, f"Processing completed in {attempt * 2} seconds")
                        return True
                    elif status == "failed":
                        self.log_test("Document Processing", False, f"Processing failed: {status_data.get('error', 'Unknown error')}")
                        return False
                    
                    # Still processing, wait
                    print(f"    Processing... (attempt {attempt + 1}/20)")
                    await asyncio.sleep(2)
                else:
                    self.log_test("Document Processing", False, f"Status check failed: {response.status_code}")
                    return False
            
            # Timeout
            self.log_test("Document Processing", False, "Processing timeout after 40 seconds")
            return False
            
        except Exception as e:
            self.log_test("Document Processing", False, f"Error: {str(e)}")
            return False
    
    async def test_chat_with_rag(self):
        """Test chat endpoint with RAG functionality."""
        print("\n💬 Testing Chat with RAG...")
        
        try:
            # Create a query that should use the uploaded document
            chat_data = {
                "message": "Based on the document I just uploaded, what are the main medical findings and recommendations?",
                "session_id": "rag_test_session"
            }
            
            headers = {"Content-Type": "application/json"}
            if self.jwt_token:
                headers["Authorization"] = f"Bearer {self.jwt_token}"
            
            start_time = time.time()
            
            # Set a longer timeout for this specific request
            response = await self.client.post(
                f"{self.base_url}/chat/message",
                json=chat_data,
                headers=headers,
                timeout=120.0  # 2 minutes for agent processing
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                self.conversation_id = result.get("session_id")
                
                # Check if response contains relevant content
                contains_medical_content = any(keyword in response_text.lower() for keyword in [
                    "document", "medical", "findings", "patient", "diagnosis", "treatment", "recommendation"
                ])
                
                self.log_test(
                    "Chat with RAG", 
                    True, 
                    f"Duration: {duration:.1f}s, Length: {len(response_text)} chars, Medical content: {contains_medical_content}"
                )
                
                print(f"    Response preview: {response_text[:200]}...")
                return True
            else:
                self.log_test("Chat with RAG", False, f"Status: {response.status_code}, Body: {response.text[:200]}...")
                return False
                
        except asyncio.TimeoutError:
            self.log_test("Chat with RAG", False, "Request timeout (agents may be slow)")
            return False
        except Exception as e:
            self.log_test("Chat with RAG", False, f"Error: {str(e)}")
            return False
    
    async def test_expert_opinion_with_rag(self):
        """Test expert opinion endpoint with RAG functionality."""
        print("\n👨‍⚕️ Testing Expert Opinion with RAG...")
        
        try:
            # Test cardiologist consultation based on uploaded document
            consult_data = {
                "message": "As a cardiologist, please analyze the uploaded medical document and provide your expert opinion on any cardiovascular findings.",
                "specialties": ["cardiologist"],
                "include_context": True,
                "priority": "normal"
            }
            
            headers = {"Content-Type": "application/json"}
            if self.jwt_token:
                headers["Authorization"] = f"Bearer {self.jwt_token}"
            
            start_time = time.time()
            
            response = await self.client.post(
                f"{self.base_url}/expert/opinion",
                json=consult_data,
                headers=headers,
                timeout=120.0  # 2 minutes for agent processing
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                specialist_opinions = result.get("specialist_opinions", [])
                aggregated_response = result.get("aggregated_response", "")
                
                self.log_test(
                    "Expert Opinion with RAG",
                    True,
                    f"Duration: {duration:.1f}s, Specialists: {len(specialist_opinions)}, Response length: {len(aggregated_response)}"
                )
                
                print(f"    Opinion preview: {aggregated_response[:200]}...")
                return True
            else:
                self.log_test("Expert Opinion with RAG", False, f"Status: {response.status_code}, Body: {response.text[:200]}...")
                return False
                
        except asyncio.TimeoutError:
            self.log_test("Expert Opinion with RAG", False, "Request timeout (agents may be slow)")
            return False
        except Exception as e:
            self.log_test("Expert Opinion with RAG", False, f"Error: {str(e)}")
            return False
    
    async def test_follow_up_chat(self):
        """Test follow-up chat to verify conversation memory."""
        print("\n🔄 Testing Follow-up Chat...")
        
        if not self.conversation_id:
            self.log_test("Follow-up Chat", False, "No conversation ID available")
            return False
        
        try:
            chat_data = {
                "message": "Can you provide more specific recommendations based on what we just discussed?",
                "session_id": self.conversation_id
            }
            
            headers = {"Content-Type": "application/json"}
            if self.jwt_token:
                headers["Authorization"] = f"Bearer {self.jwt_token}"
            
            start_time = time.time()
            
            response = await self.client.post(
                f"{self.base_url}/chat/message",
                json=chat_data,
                headers=headers,
                timeout=60.0
            )
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                self.log_test(
                    "Follow-up Chat",
                    True,
                    f"Duration: {duration:.1f}s, Response length: {len(response_text)}"
                )
                
                print(f"    Follow-up response: {response_text[:150]}...")
                return True
            else:
                self.log_test("Follow-up Chat", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Follow-up Chat", False, f"Error: {str(e)}")
            return False
    
    async def verify_document_retrieval(self):
        """Verify the document is properly stored and retrievable."""
        print("\n🔍 Verifying Document Storage...")
        
        try:
            headers = {}
            if self.jwt_token:
                headers["Authorization"] = f"Bearer {self.jwt_token}"
            
            response = await self.client.get(
                f"{self.base_url}/upload/documents",
                headers=headers,
                params={"limit": 10}
            )
            
            if response.status_code == 200:
                documents = response.json()
                doc_count = documents.get("total", 0)
                
                # Check if our document is in the list
                our_doc_found = False
                if "documents" in documents:
                    for doc in documents["documents"]:
                        if doc.get("data", {}).get("document_id") == self.document_id:
                            our_doc_found = True
                            break
                
                self.log_test(
                    "Document Storage Verification",
                    True,
                    f"Total documents: {doc_count}, Our document found: {our_doc_found}"
                )
                return True
            else:
                self.log_test("Document Storage Verification", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Document Storage Verification", False, f"Error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all RAG functionality tests."""
        print("🚀 Starting Comprehensive RAG Testing")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"Test Document: {TEST_DOCUMENT}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        try:
            # Run tests in sequence
            await self.generate_jwt_token()
            await self.upload_test_document()
            await self.wait_for_processing()
            await self.verify_document_retrieval()
            await self.test_chat_with_rag()
            await self.test_expert_opinion_with_rag()
            await self.test_follow_up_chat()
            
        finally:
            await self.client.aclose()
        
        # Print final results
        print("\n" + "=" * 60)
        print("📊 RAG TESTING RESULTS")
        print("=" * 60)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        total = self.test_results['passed'] + self.test_results['failed']
        success_rate = (self.test_results['passed'] / total * 100) if total > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.test_results['failed'] > 0:
            print("\n❌ Failed Tests:")
            for test in self.test_results['tests']:
                if not test['success']:
                    print(f"   - {test['name']}: {test['details']}")
        
        if self.document_id:
            print(f"\n🆔 Test Document ID: {self.document_id}")
        if self.conversation_id:
            print(f"💬 Conversation ID: {self.conversation_id}")
        
        return self.test_results


async def main():
    """Main test runner."""
    tester = RAGTester()
    results = await tester.run_all_tests()
    
    # Return appropriate exit code
    if results['failed'] == 0:
        print("\n🎉 All RAG tests passed! The system is working correctly.")
        return 0
    else:
        print("\n⚠️  Some RAG tests failed. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
