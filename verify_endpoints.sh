#!/bin/bash
"""
Simple endpoint verification script using grep.
"""

echo "🔍 MediTwin Agents Backend Endpoint Verification"
echo "=================================================="
echo

# Check key endpoints exist
echo "📋 Essential Endpoints Check:"
echo "------------------------------"

# Chat endpoints
echo -n "💬 Chat endpoints: "
if grep -q "@router.post.*message" src/api/v1/endpoints/chat.py; then
    echo "✅ Found chat message endpoint"
else
    echo "❌ Missing chat message endpoint"
fi

# Expert Opinion endpoints  
echo -n "🔬 Expert opinion: "
if grep -q "@router.post.*expert-opinion" src/api/v1/endpoints/expert_opinion.py; then
    echo "✅ Found expert opinion endpoint"
else
    echo "❌ Missing expert opinion endpoint"
fi

# Body parts endpoints
echo -n "🫀 Body parts: "
if grep -q "@router.get.*body-parts" src/api/v1/endpoints/anatomy.py; then
    echo "✅ Found body parts endpoint"
else
    echo "❌ Missing body parts endpoint"
fi

# Timeline endpoints
echo -n "📅 Timeline: "
if grep -q "@router.get.*timeline" src/api/v1/endpoints/timeline.py; then
    echo "✅ Found timeline endpoint"
else
    echo "❌ Missing timeline endpoint"
fi

# Year-specific timeline
echo -n "📆 Year timeline: "
if grep -q "@router.get.*/{year}" src/api/v1/endpoints/timeline.py; then
    echo "✅ Found year-specific timeline"
else
    echo "❌ Missing year-specific timeline"
fi

# Region endpoints
echo -n "🗺️  Region summary: "
if grep -q "@router.get.*/region/" src/api/v1/endpoints/anatomy.py; then
    echo "✅ Found region endpoints"
else
    echo "❌ Missing region endpoints"
fi

# Export endpoints
echo -n "📄 PDF export: "
if grep -q "@router.get.*/health/export" src/api/v1/endpoints/export.py; then
    echo "✅ Found PDF export endpoint"
else
    echo "❌ Missing PDF export endpoint"
fi

# Document upload
echo -n "📤 Document upload: "
if grep -q "@router.post.*upload" src/api/v1/endpoints/documents.py; then
    echo "✅ Found document upload"
else
    echo "❌ Missing document upload"
fi

# Admin endpoints
echo -n "🔐 Admin endpoints: "
if grep -q "@router.delete.*patient" src/api/v1/endpoints/admin.py; then
    echo "✅ Found admin delete endpoint"
else
    echo "❌ Missing admin delete endpoint"
fi

echo
echo "🛡️  Security Verification:"
echo "---------------------------"

# Check for CurrentUser dependency
echo -n "🔒 Authentication: "
current_user_count=$(grep -r "CurrentUser" src/api/v1/endpoints/ | wc -l)
echo "Found $current_user_count endpoints using CurrentUser"

# Check for AuthenticatedPatientId
echo -n "🆔 Patient ID auth: "
patient_id_count=$(grep -r "AuthenticatedPatientId" src/api/v1/endpoints/ | wc -l)
echo "Found $patient_id_count endpoints using AuthenticatedPatientId"

echo
echo "🗂️  Database Integration:"
echo "--------------------------"

# Neo4j usage
echo -n "🌐 Neo4j: "
neo4j_count=$(grep -r "neo4j_client\|get_graph" src/api/v1/endpoints/ | wc -l)
echo "Found $neo4j_count Neo4j interactions"

# MongoDB usage  
echo -n "🍃 MongoDB: "
mongo_count=$(grep -r "mongo_client\|get_mongo" src/api/v1/endpoints/ | wc -l)
echo "Found $mongo_count MongoDB interactions"

# Milvus usage
echo -n "🔍 Milvus: "
milvus_count=$(grep -r "milvus_client\|get_milvus" src/api/v1/endpoints/ | wc -l)
echo "Found $milvus_count Milvus interactions"

echo
echo "✅ Verification Complete!"
