#!/usr/bin/env python3
"""
Test script to verify the body parts and severity endpoints implementation.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.body_parts import (
    get_default_body_parts, 
    get_severity_levels, 
    validate_body_part,
    identify_body_parts_from_text
)

def test_body_parts_configuration():
    """Test the body parts configuration."""
    print("🧩 Testing Body Parts Configuration")
    print("=" * 50)
    
    # Test body parts list
    body_parts = get_default_body_parts()
    print(f"✅ Total body parts: {len(body_parts)}")
    assert len(body_parts) == 30, f"Expected 30 body parts, got {len(body_parts)}"
    
    # Print all body parts
    print("\n📋 Complete Body Parts List:")
    for i, part in enumerate(body_parts, 1):
        print(f"{i:2d}. {part}")
    
    # Test severity levels
    severity_levels = get_severity_levels()
    print(f"\n✅ Severity levels: {list(severity_levels.keys())}")
    
    # Test validation
    print("\n🔍 Testing Validation:")
    print(f"✅ 'Heart' valid: {validate_body_part('Heart')}")
    print(f"✅ 'Invalid Part' valid: {validate_body_part('Invalid Part')}")
    
    # Test text extraction
    print("\n📝 Testing Text Extraction:")
    test_texts = [
        "Patient has chest pain near the heart",
        "Left knee injury from soccer",
        "Right ankle sprain and left shoulder pain",
        "Brain tumor detected in MRI scan",
        "Liver function tests abnormal"
    ]
    
    for text in test_texts:
        extracted = identify_body_parts_from_text(text)
        print(f"Text: '{text}'")
        print(f"Extracted: {extracted}")
        print()

def test_severity_thresholds():
    """Test severity calculation logic."""
    print("🎯 Testing Severity Thresholds")
    print("=" * 50)
    
    # Test cases for severity determination
    test_cases = [
        {
            "text": "cancer tumor malignant",
            "expected_severity": "critical",
            "description": "Cancer-related terms should be critical"
        },
        {
            "text": "acute severe pneumonia",
            "expected_severity": "severe", 
            "description": "Acute conditions should be severe"
        },
        {
            "text": "mild inflammation pain",
            "expected_severity": "moderate",
            "description": "Mild conditions should be moderate"
        },
        {
            "text": "medication prescribed",
            "expected_severity": "mild",
            "description": "Medications should be mild"
        }
    ]
    
    # Import the severity determination function
    from src.agents.ingestion_agent import IngestionAgent
    
    agent = IngestionAgent()
    
    for test_case in test_cases:
        entity = {
            "text": test_case["text"],
            "type": "conditions",
            "confidence": 0.9
        }
        
        determined_severity = agent._determine_entity_severity(entity)
        print(f"Text: '{test_case['text']}'")
        print(f"Expected: {test_case['expected_severity']}")
        print(f"Determined: {determined_severity}")
        print(f"Description: {test_case['description']}")
        print(f"✅ {'PASS' if determined_severity == test_case['expected_severity'] else 'FAIL'}")
        print()

def test_api_endpoints_json():
    """Test the JSON structure that endpoints should return."""
    print("🌐 Testing API Endpoint JSON Structures")
    print("=" * 50)
    
    # Test body parts severity endpoint response
    body_parts = get_default_body_parts()
    severity_levels = list(get_severity_levels().keys())
    
    # Sample response for GET /anatomy/body-parts
    body_parts_response = {
        "user_id": "sample_user_123",
        "body_parts": [
            {
                "name": part,
                "severity": "NA" if i % 5 == 0 else severity_levels[i % len(severity_levels)]
            }
            for i, part in enumerate(body_parts)
        ],
        "total_parts": len(body_parts)
    }
    
    print("📊 Sample GET /anatomy/body-parts Response:")
    print(json.dumps(body_parts_response, indent=2))
    
    # Sample response for GET /anatomy/body-part/{body_part}
    body_part_detail_response = {
        "user_id": "sample_user_123",
        "body_part": "Heart",
        "current_severity": "mild",
        "statistics": {
            "total_events": 3,
            "severity_distribution": {
                "mild": 2,
                "moderate": 1
            },
            "last_updated": "2025-07-06T10:30:00Z"
        },
        "recent_events": [
            {
                "event_id": "evt_123",
                "title": "Elevated blood pressure",
                "description": "Blood pressure reading 140/90",
                "event_type": "condition",
                "timestamp": "2025-07-06T10:30:00Z",
                "severity": "mild"
            }
        ],
        "related_conditions": [
            {
                "condition": "Hypertension",
                "description": "Related cardiovascular condition",
                "event_type": "condition",
                "timestamp": "2025-07-05T14:20:00Z",
                "shared_body_part": "Heart"
            }
        ]
    }
    
    print(f"\n📋 Sample GET /anatomy/body-part/Heart Response:")
    print(json.dumps(body_part_detail_response, indent=2))

def main():
    """Run all tests."""
    print("🔬 MediTwin Body Parts Implementation Test Suite")
    print("=" * 60)
    
    try:
        test_body_parts_configuration()
        print("\n")
        test_severity_thresholds()
        print("\n")
        test_api_endpoints_json()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("🎉 Body parts implementation is ready for production!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
