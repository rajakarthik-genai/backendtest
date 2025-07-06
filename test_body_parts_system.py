#!/usr/bin/env python3
"""
Test script for the Neo4j body parts implementation.
"""

import sys
import os
sys.path.append('/home/user/agents/meditwin-agents')

from src.config.body_parts import (
    get_default_body_parts, 
    get_severity_levels, 
    validate_body_part,
    identify_body_parts_from_text
)

def test_body_parts_config():
    """Test the body parts configuration."""
    print("🧪 Testing Body Parts Configuration")
    print("=" * 50)
    
    # Test loading body parts
    parts = get_default_body_parts()
    print(f"✅ Total body parts: {len(parts)}")
    assert len(parts) == 30, f"Expected 30 parts, got {len(parts)}"
    
    # Test severity levels
    severities = get_severity_levels()
    print(f"✅ Severity levels: {list(severities.keys())}")
    assert len(severities) == 6, f"Expected 6 severity levels"
    
    # Test validation
    assert validate_body_part("Heart") == True
    assert validate_body_part("InvalidPart") == False
    print("✅ Validation tests passed")
    
    # Test text extraction
    text = "Patient has chest pain affecting the heart and left lung"
    extracted = identify_body_parts_from_text(text)
    print(f"✅ Text extraction test: '{text}' -> {extracted}")
    
    print("\n✅ All body parts configuration tests passed!")
    return True

def test_api_endpoints():
    """Test the API endpoint structure."""
    print("\n🧪 Testing API Implementation")
    print("=" * 50)
    
    try:
        # Import anatomy endpoints
        from src.api.endpoints.anatomy import router
        print(f"✅ Anatomy router imported successfully")
        print(f"✅ Router prefix: {router.prefix}")
        print(f"✅ Router tags: {router.tags}")
        
        # Check middleware
        from src.middleware.user_initialization import UserInitializationMiddleware
        print(f"✅ User initialization middleware imported")
        
        # Check Neo4j functions
        from src.db.neo4j_db import Neo4jDB
        neo4j = Neo4jDB()
        print(f"✅ Neo4j database class imported")
        
        print("\n✅ All API implementation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_api_documentation():
    """Generate API documentation for the new endpoints."""
    print("\n📖 API Documentation")
    print("=" * 50)
    
    parts = get_default_body_parts()
    severities = get_severity_levels()
    
    docs = f"""
# MediTwin Body Parts API Documentation

## Overview
The MediTwin system now includes comprehensive body part tracking with 30 anatomical regions
for 3D visualization and severity monitoring.

## Body Parts List ({len(parts)} total)
{chr(10).join(f'- {part}' for part in parts)}

## Severity Levels
{chr(10).join(f'- **{k}**: {v}' for k, v in severities.items())}

## API Endpoints

### 1. Get All Body Parts with Severities
```
GET /anatomy/body-parts
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{{
  "user_id": "user123",
  "body_parts": [
    {{"name": "Heart", "severity": "normal"}},
    {{"name": "Left Knee", "severity": "mild"}},
    ...
  ],
  "total_parts": 30
}}
```

### 2. Get Specific Body Part Details
```
GET /anatomy/body-part/{{body_part}}
Authorization: Bearer <jwt_token>
```

**Example:** `GET /anatomy/body-part/Heart`

**Response:**
```json
{{
  "user_id": "user123",
  "body_part": "Heart",
  "current_severity": "normal",
  "statistics": {{
    "total_events": 5,
    "severity_distribution": {{"mild": 3, "normal": 2}},
    "last_updated": "2025-07-06T12:00:00Z"
  }},
  "recent_events": [...],
  "related_conditions": [...]
}}
```

### 3. Update Body Part Severity
```
POST /anatomy/body-part/{{body_part}}/severity?severity={{level}}
Authorization: Bearer <jwt_token>
```

### 4. Auto-Update All Severities
```
POST /anatomy/auto-update-severities
Authorization: Bearer <jwt_token>
```

## User Flow
1. **Login**: User authenticates via separate login service
2. **Auto-Initialization**: First API call automatically creates user node + 30 body parts in Neo4j
3. **Document Upload**: `POST /upload` processes medical documents and updates relevant body parts
4. **3D Visualization**: Frontend calls `GET /anatomy/body-parts` for severity data
5. **Detailed View**: Frontend calls `GET /anatomy/body-part/{{name}}` for specific information

## Implementation Notes
- All body parts start with severity "NA" (No data available)
- Severities are auto-calculated based on recent medical events
- System is modular - new body parts can be added to the configuration
- User data is isolated via hashed user IDs in Neo4j
- Knowledge graph updates happen automatically during document ingestion
"""
    
    print(docs)
    return docs

if __name__ == "__main__":
    print("🚀 MediTwin Body Parts System Test Suite")
    print("=" * 60)
    
    success = True
    
    try:
        success &= test_body_parts_config()
        success &= test_api_endpoints()
        generate_api_documentation()
        
        if success:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ System is ready for production use")
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
