#!/usr/bin/env python3
"""
Test script for LLM-powered medical entity extraction.
This script tests the new OpenAI-based extraction pipeline.
"""

import asyncio
import json
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agents.ingestion_agent import IngestionAgent
from src.utils.logging import logger

# Sample medical document text for testing
SAMPLE_MEDICAL_DOCUMENT = """
PATIENT: John Doe
DATE: 2025-01-15
DEPARTMENT: Cardiology

CHIEF COMPLAINT:
Patient presents with chest pain and shortness of breath.

HISTORY OF PRESENT ILLNESS:
The patient is a 65-year-old male with a history of hypertension and diabetes mellitus type 2. 
He reports experiencing severe chest pain radiating to his left arm for the past 2 hours. 
The pain is described as crushing and is associated with nausea and diaphoresis.

PHYSICAL EXAMINATION:
- Vital signs: BP 160/95, HR 110, RR 22, O2 sat 92%
- Heart: Irregular rhythm, murmur present
- Lungs: Bilateral crackles in lower lobes
- Extremities: Mild edema in both legs

DIAGNOSTIC RESULTS:
- ECG: ST-elevation in leads II, III, aVF
- Chest X-ray: Cardiomegaly, pulmonary edema
- Troponin: Elevated at 15.2 ng/mL

ASSESSMENT:
1. Acute ST-elevation myocardial infarction (STEMI)
2. Acute heart failure
3. Hypertension - uncontrolled
4. Diabetes mellitus type 2 - stable

PLAN:
1. Emergent cardiac catheterization
2. Aspirin 325mg, Clopidogrel 600mg loading dose
3. Heparin per protocol
4. Furosemide 40mg IV for heart failure
5. Metformin hold, insulin sliding scale
6. Cardiology consultation

PROGNOSIS:
Guarded given extent of myocardial damage. Patient requires intensive monitoring.
"""

async def test_llm_extraction():
    """Test the LLM-powered medical entity extraction."""
    print("🔬 Testing LLM-Powered Medical Entity Extraction")
    print("=" * 60)
    
    try:
        # Initialize the ingestion agent
        agent = IngestionAgent()
        
        # Test entity extraction
        print("\n📝 Sample Medical Document:")
        print("-" * 40)
        print(SAMPLE_MEDICAL_DOCUMENT[:300] + "..." if len(SAMPLE_MEDICAL_DOCUMENT) > 300 else SAMPLE_MEDICAL_DOCUMENT)
        
        print("\n🤖 Extracting entities with LLM...")
        entities = await agent._extract_medical_entities(SAMPLE_MEDICAL_DOCUMENT)
        
        print(f"\n✅ Extracted {len(entities)} entities:")
        print("-" * 40)
        
        for i, entity in enumerate(entities, 1):
            print(f"\n{i}. Entity:")
            print(f"   Body Part: {entity.get('body_part', 'N/A')}")
            print(f"   Condition: {entity.get('condition', entity.get('text', 'N/A'))}")
            print(f"   Severity: {entity.get('severity', 'N/A')}")
            print(f"   Confidence: {entity.get('confidence', 'N/A')}")
            print(f"   Method: {entity.get('extraction_method', 'N/A')}")
            if entity.get('description'):
                print(f"   Description: {entity.get('description')}")
            if entity.get('date'):
                print(f"   Date: {entity.get('date')}")
        
        print("\n📊 Extraction Summary:")
        print("-" * 40)
        
        # Analyze extraction results
        methods = {}
        severities = {}
        body_parts = {}
        
        for entity in entities:
            method = entity.get('extraction_method', 'unknown')
            severity = entity.get('severity', 'unknown')
            body_part = entity.get('body_part', entity.get('text', 'unknown'))
            
            methods[method] = methods.get(method, 0) + 1
            severities[severity] = severities.get(severity, 0) + 1
            body_parts[body_part] = body_parts.get(body_part, 0) + 1
        
        print(f"Extraction Methods: {methods}")
        print(f"Severity Distribution: {severities}")
        print(f"Body Parts Found: {list(body_parts.keys())}")
        
        # Test JSON serialization
        print("\n🔧 Testing JSON Serialization:")
        try:
            json_output = json.dumps(entities, indent=2, default=str)
            print("✅ JSON serialization successful")
            print(f"📏 JSON size: {len(json_output)} characters")
        except Exception as e:
            print(f"❌ JSON serialization failed: {e}")
        
        return entities
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_fallback_extraction():
    """Test the fallback keyword extraction."""
    print("\n🔄 Testing Fallback Keyword Extraction")
    print("=" * 60)
    
    try:
        agent = IngestionAgent()
        
        # Test fallback method directly
        simple_text = "Patient has heart pain and diabetes. Lung infection detected."
        
        print(f"\n📝 Simple test text: {simple_text}")
        print("\n🔍 Using fallback extraction...")
        
        entities = await agent._fallback_keyword_extraction(simple_text)
        
        print(f"\n✅ Fallback extracted {len(entities)} entities:")
        for i, entity in enumerate(entities, 1):
            print(f"{i}. {entity.get('text', 'N/A')} ({entity.get('category', 'N/A')}) - {entity.get('confidence', 'N/A')}")
        
        return entities
        
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return None

async def test_document_processing():
    """Test the complete document processing pipeline."""
    print("\n🏭 Testing Complete Document Processing Pipeline")
    print("=" * 60)
    
    try:
        agent = IngestionAgent()
        
        # Create a temporary file with medical text
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(SAMPLE_MEDICAL_DOCUMENT)
            temp_file = f.name
        
        print(f"\n📄 Created temporary file: {temp_file}")
        
        # Test the complete processing pipeline
        print("\n🔄 Processing document...")
        
        result = await agent.process_document(
            user_id="test_user_123",
            document_id="test_doc_456",
            file_path=temp_file,
            metadata={"type": "medical_report", "test": True}
        )
        
        print(f"\n✅ Processing result:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Entities: {len(result.get('entities', []))}")
        print(f"   Text Length: {result.get('text_length', 0)}")
        
        if result.get('entities'):
            print(f"\n📋 Extracted entities:")
            for i, entity in enumerate(result.get('entities', [])[:5], 1):  # Show first 5
                print(f"   {i}. {entity.get('condition', entity.get('text', 'N/A'))} → {entity.get('body_part', 'N/A')}")
        
        # Clean up
        os.unlink(temp_file)
        
        return result
        
    except Exception as e:
        print(f"❌ Document processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Run all tests."""
    print("🚀 LLM-Powered Medical Entity Extraction Test Suite")
    print("=" * 60)
    print("This script tests the new OpenAI-based extraction pipeline.")
    print("Make sure OPENAI_API_KEY is set in your environment.\n")
    
    # Check for OpenAI API key
    import os
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("Please set it and run again:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    try:
        # Test 1: LLM Extraction
        entities = await test_llm_extraction()
        
        # Test 2: Fallback Extraction
        fallback_entities = await test_fallback_extraction()
        
        # Test 3: Complete Pipeline
        processing_result = await test_document_processing()
        
        print("\n🎯 Test Summary:")
        print("=" * 60)
        print(f"✅ LLM Extraction: {'PASSED' if entities else 'FAILED'}")
        print(f"✅ Fallback Extraction: {'PASSED' if fallback_entities else 'FAILED'}")
        print(f"✅ Document Processing: {'PASSED' if processing_result and processing_result.get('success') else 'FAILED'}")
        
        if entities:
            print(f"\n📈 Performance Metrics:")
            print(f"   Total entities extracted: {len(entities)}")
            print(f"   LLM method used: {'Yes' if any(e.get('extraction_method') == 'llm_structured_output' for e in entities) else 'No'}")
            print(f"   Average confidence: {sum(e.get('confidence', 0) for e in entities) / len(entities):.2f}")
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
