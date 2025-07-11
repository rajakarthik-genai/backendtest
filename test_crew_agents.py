#!/usr/bin/env python3
"""
Test script for the CrewAI multi-agent document processing system.

This script demonstrates how to use the new comprehensive medical document 
extraction and storage pipeline.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents.crew_agents import MedicalDocumentCrew, process_medical_document
from src.utils.logging import logger


async def test_document_processing():
    """Test the complete document processing pipeline."""
    
    print("🏥 MediTwin CrewAI Multi-Agent Document Processing Test")
    print("=" * 60)
    
    # Test configuration
    test_user_id = "test_user_123"
    test_document_id = "test_doc_001"
    test_file_path = "test_upload.pdf"  # Your uploaded test file
    
    # Check if test file exists
    if not os.path.exists(test_file_path):
        print(f"❌ Test file not found: {test_file_path}")
        print("Please ensure you have a PDF file named 'test_upload.pdf' in the current directory")
        return
    
    print(f"📄 Processing document: {test_file_path}")
    print(f"👤 User ID: {test_user_id}")
    print(f"🆔 Document ID: {test_document_id}")
    print()
    
    try:
        # Initialize the CrewAI system
        print("🔧 Initializing CrewAI Multi-Agent System...")
        crew = MedicalDocumentCrew()
        
        # Validate document
        validation = crew.validate_document(test_file_path)
        print(f"✅ Document validation: {validation}")
        
        if not validation["valid"]:
            print(f"❌ Document validation failed: {validation['error']}")
            return
        
        print("\n🚀 Starting document processing pipeline...")
        print("This will run through all 4 agents:")
        print("  1. 📖 Document Reader (PDF extraction + OCR)")
        print("  2. 🧠 Clinical Extractor (Medical entity extraction)")
        print("  3. 🔍 Vector Embedder (Semantic embeddings)")
        print("  4. 💾 Storage Coordinator (Multi-database storage)")
        print()
        
        # Process document
        result = await crew.process_document(
            user_id=test_user_id,
            document_id=test_document_id,
            file_path=test_file_path,
            metadata={
                "test_run": True,
                "source": "test_script"
            }
        )
        
        # Display results
        print("\n📊 PROCESSING RESULTS")
        print("=" * 40)
        
        if result["success"]:
            print("✅ Processing completed successfully!")
            
            summary = result.get("summary", {})
            print(f"📝 Text extracted: {summary.get('text_extracted', 0)} characters")
            print(f"🩹 Injuries found: {summary.get('injuries_found', 0)}")
            print(f"🔬 Diagnoses found: {summary.get('diagnoses_found', 0)}")
            print(f"⚕️  Procedures found: {summary.get('procedures_found', 0)}")
            print(f"💊 Medications found: {summary.get('medications_found', 0)}")
            print(f"🔍 Embeddings created: {summary.get('embeddings_created', 0)}")
            print(f"💾 Storage systems updated: {summary.get('storage_systems_updated', 0)}")
            print(f"⏱️  Processing time: {result.get('processing_duration_seconds', 0):.2f} seconds")
            
            # Show stage details
            print("\n🔍 STAGE DETAILS")
            print("-" * 30)
            
            stages = result.get("stages", {})
            for stage_name, stage_result in stages.items():
                status = "✅" if stage_result.get("success", False) else "❌"
                print(f"{status} {stage_name.replace('_', ' ').title()}")
                
                if not stage_result.get("success", False):
                    print(f"    Error: {stage_result.get('error', 'Unknown error')}")
            
        else:
            print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
            
            # Show partial results if available
            stages = result.get("stages", {})
            if stages:
                print("\n📋 Partial results:")
                for stage_name, stage_result in stages.items():
                    status = "✅" if stage_result.get("success", False) else "❌"
                    print(f"  {status} {stage_name.replace('_', ' ').title()}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        logger.error(f"Test script failed: {e}")


def test_sync_processing():
    """Test synchronous document processing."""
    
    print("\n🔄 Testing Synchronous Processing...")
    
    test_user_id = "test_user_sync"
    test_document_id = "test_doc_sync"
    test_file_path = "test_upload.pdf"
    
    if not os.path.exists(test_file_path):
        print(f"❌ Test file not found: {test_file_path}")
        return
    
    try:
        # Process document synchronously
        result = process_medical_document(
            user_id=test_user_id,
            document_id=test_document_id,
            file_path=test_file_path,
            metadata={"test_run": True, "sync": True}
        )
        
        if result["success"]:
            print("✅ Synchronous processing completed!")
            summary = result.get("summary", {})
            print(f"⏱️  Processing time: {result.get('processing_duration_seconds', 0):.2f} seconds")
        else:
            print(f"❌ Synchronous processing failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Synchronous test failed: {e}")


async def test_individual_agents():
    """Test individual agents separately."""
    
    print("\n🧪 Testing Individual Agents...")
    
    test_file_path = "test_upload.pdf"
    
    if not os.path.exists(test_file_path):
        print(f"❌ Test file not found: {test_file_path}")
        return
    
    try:
        from src.agents.crew_agents import (
            DocumentReaderAgent, 
            ClinicalExtractorAgent,
            VectorEmbeddingAgent,
            StorageCoordinatorAgent
        )
        
        # Test Document Reader
        print("\n📖 Testing Document Reader Agent...")
        reader = DocumentReaderAgent()
        text_result = reader.extract_document_text(test_file_path, "test_doc")
        
        if text_result["success"]:
            print(f"✅ Text extraction: {len(text_result.get('full_text', ''))} characters")
            print(f"📄 Pages processed: {text_result.get('metadata', {}).get('page_count', 0)}")
        else:
            print(f"❌ Text extraction failed: {text_result['error']}")
            return
        
        # Test Clinical Extractor
        print("\n🧠 Testing Clinical Extractor Agent...")
        extractor = ClinicalExtractorAgent()
        clinical_result = extractor.extract_clinical_data(text_result, "test_doc")
        
        if clinical_result["success"]:
            clinical_data = clinical_result["clinical_data"]
            print(f"✅ Clinical extraction completed")
            print(f"🩹 Injuries: {len(clinical_data.get('injuries', []))}")
            print(f"🔬 Diagnoses: {len(clinical_data.get('diagnoses', []))}")
        else:
            print(f"❌ Clinical extraction failed: {clinical_result['error']}")
            return
        
        # Test Vector Embedder
        print("\n🔍 Testing Vector Embedding Agent...")
        embedder = VectorEmbeddingAgent()
        embedding_result = embedder.process_embeddings(clinical_data, "test_doc")
        
        if embedding_result["success"]:
            print(f"✅ Embedding generation: {embedding_result.get('embeddings_stored', 0)} vectors")
        else:
            print(f"❌ Embedding failed: {embedding_result['error']}")
        
        # Test Storage Coordinator
        print("\n💾 Testing Storage Coordinator Agent...")
        coordinator = StorageCoordinatorAgent()
        storage_result = coordinator.coordinate_storage(clinical_data, "test_doc", "test_user")
        
        if storage_result["success"]:
            print(f"✅ Storage coordination: {storage_result.get('successful_systems', 0)} systems updated")
        else:
            print(f"❌ Storage coordination failed: {storage_result.get('error')}")
        
    except Exception as e:
        print(f"❌ Individual agent testing failed: {e}")


def print_usage_instructions():
    """Print usage instructions for the system."""
    
    print("\n📋 USAGE INSTRUCTIONS")
    print("=" * 50)
    print()
    print("🔧 SETUP:")
    print("1. Ensure all dependencies are installed: pip install -r requirements.txt")
    print("2. Configure environment variables in .env file")
    print("3. Start MongoDB, Neo4j, and Milvus services")
    print("4. Place your test PDF file as 'test_upload.pdf'")
    print()
    print("🚀 API USAGE:")
    print("1. Start the server: python -m src.main")
    print("2. Upload documents via POST /documents/upload")
    print("3. Check processing status via GET /documents/status/{document_id}")
    print("4. Retrieve processed data via GET /documents/detail/{document_id}")
    print()
    print("🔍 QUERYING DATA:")
    print("1. View timeline: GET /timeline/")
    print("2. Check body part status: GET /anatomy/body-parts")
    print("3. Get body part history: GET /timeline/{user_id}/{body_part}")
    print()
    print("🧠 AI CHAT:")
    print("1. Chat with medical specialists: POST /chat/")
    print("2. Get expert opinions: POST /expert-opinion/")
    print()


async def main():
    """Main test function."""
    
    print("🔬 MediTwin CrewAI Multi-Agent System Test Suite")
    print("===============================================")
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == "full":
            await test_document_processing()
        elif test_type == "sync":
            test_sync_processing()
        elif test_type == "agents":
            await test_individual_agents()
        elif test_type == "usage":
            print_usage_instructions()
        else:
            print(f"Unknown test type: {test_type}")
            print("Available options: full, sync, agents, usage")
    else:
        print("🔄 Running full test suite...")
        await test_document_processing()
        test_sync_processing()
        await test_individual_agents()
        print_usage_instructions()


if __name__ == "__main__":
    asyncio.run(main())
