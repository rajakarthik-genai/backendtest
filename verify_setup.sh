#!/bin/bash
# Quick verification script for MediTwin Frontend

echo "🚀 MediTwin Frontend - Quick Verification"
echo "========================================"

# Check if required services are running
echo "🔍 Checking required services..."

# Check Backend Auth Service (port 8081)
if curl -s http://localhost:8081/health > /dev/null 2>&1; then
    echo "✅ Backend Auth Service (port 8081) - Running"
else
    echo "❌ Backend Auth Service (port 8081) - Not accessible"
fi

# Check Agents Service (port 8000)
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Agents Service (port 8000) - Running"
else
    echo "❌ Agents Service (port 8000) - Not accessible"
fi

# Check Python dependencies
echo "🔍 Checking Python dependencies..."
if python3 -c "import requests" 2>/dev/null; then
    echo "✅ Python requests library - Available"
else
    echo "❌ Python requests library - Missing (install with: pip install requests)"
fi

# Verify test file syntax
echo "🔍 Checking test file..."
if python3 -m py_compile complete_user_journey_test.py 2>/dev/null; then
    echo "✅ Test file syntax - Valid"
else
    echo "❌ Test file syntax - Invalid"
fi

echo ""
echo "📋 To run the complete test suite:"
echo "   python3 complete_user_journey_test.py"
echo ""
echo "📖 For more information, see README.md"
