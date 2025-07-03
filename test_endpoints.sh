#!/bin/bash
"""
Comprehensive API Endpoint Testing Script using curl

This script tests all MediTwin backend endpoints using curl commands.
"""

BASE_URL="http://localhost:8000"
TEST_USER_ID="test_user_$(date +%s)"
CONVERSATION_ID="conv_$(date +%s)"

echo "============================================================="
echo "🧪 MEDITWIN BACKEND ENDPOINT TESTING"
echo "============================================================="
echo "📅 Test Date: $(date)"
echo "🔗 Base URL: $BASE_URL"
echo "👤 Test User ID: $TEST_USER_ID"
echo "-------------------------------------------------------------"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_endpoint() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    local expected_codes="$5"
    
    echo -e "\n🔍 Testing: $name"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" "$url" 2>/dev/null)
    elif [ "$method" = "POST" ]; then
        if [ -n "$data" ]; then
            response=$(curl -s -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$url" 2>/dev/null)
        else
            response=$(curl -s -w "%{http_code}" -X POST "$url" 2>/dev/null)
        fi
    fi
    
    # Extract status code (last 3 characters)
    status_code="${response: -3}"
    # Extract response body (everything except last 3 characters)
    response_body="${response%???}"
    
    echo "   Status Code: $status_code"
    
    # Check if status code is expected
    if echo "$expected_codes" | grep -q "$status_code"; then
        echo -e "   ${GREEN}✅ PASS${NC} - Expected status code"
    else
        echo -e "   ${RED}❌ FAIL${NC} - Unexpected status code (expected: $expected_codes)"
    fi
    
    # Show response body if it's reasonable length and valid JSON
    if [ ${#response_body} -lt 500 ] && echo "$response_body" | jq . >/dev/null 2>&1; then
        echo "   Response: $(echo "$response_body" | jq -c .)"
    elif [ ${#response_body} -lt 200 ]; then
        echo "   Response: $response_body"
    fi
}

echo -e "\n🏥 HEALTH CHECK"
test_endpoint "Health Check" "GET" "$BASE_URL/health" "" "200"

echo -e "\n📚 API DOCUMENTATION"
test_endpoint "OpenAPI Docs" "GET" "$BASE_URL/docs" "" "200"
test_endpoint "OpenAPI JSON" "GET" "$BASE_URL/openapi.json" "" "200"

echo -e "\n🔐 AUTHENTICATION ENDPOINTS"
test_endpoint "Login (Invalid)" "POST" "$BASE_URL/auth/login" '{"username":"test@example.com","password":"invalid"}' "400 401 422"
test_endpoint "Register" "POST" "$BASE_URL/auth/register" '{"email":"test@example.com","username":"testuser","password":"testpass123"}' "200 400 409 422"
test_endpoint "Refresh Token" "POST" "$BASE_URL/auth/refresh" '{"refresh_token":"invalid_token"}' "400 401 422"

echo -e "\n📄 UPLOAD ENDPOINTS"
# Create a test file
echo "Test medical document content" > /tmp/test_doc.txt
test_endpoint "Upload Status Check" "GET" "$BASE_URL/upload/status/test_id" "" "200 404 422"

echo -e "\n💬 CHAT ENDPOINTS"
chat_data="{\"message\":\"What is the patient's condition?\",\"conversation_id\":\"$CONVERSATION_ID\",\"user_id\":\"$TEST_USER_ID\"}"
test_endpoint "Chat Message" "POST" "$BASE_URL/chat" "$chat_data" "200 422 500"
test_endpoint "Chat History" "GET" "$BASE_URL/chat/history?conversation_id=$CONVERSATION_ID&user_id=$TEST_USER_ID" "" "200 422"

echo -e "\n🩺 EXPERT OPINION ENDPOINTS"
expert_data="{\"query\":\"Provide cardiology consultation for chest pain\",\"specialist\":\"cardiologist\",\"user_id\":\"$TEST_USER_ID\"}"
test_endpoint "Expert Opinion" "POST" "$BASE_URL/expert-opinion" "$expert_data" "200 422 500"
test_endpoint "Available Specialists" "GET" "$BASE_URL/expert-opinion/specialists" "" "200 404"

echo -e "\n📅 TIMELINE ENDPOINTS"
test_endpoint "Timeline" "GET" "$BASE_URL/timeline?user_id=$TEST_USER_ID&start_date=2024-01-01&end_date=2024-12-31" "" "200 422"
event_data="{\"event_type\":\"symptom\",\"description\":\"Test symptom\",\"date\":\"2024-01-01T12:00:00\",\"user_id\":\"$TEST_USER_ID\"}"
test_endpoint "Add Timeline Event" "POST" "$BASE_URL/timeline/events" "$event_data" "200 422"

echo -e "\n🫀 ANATOMY ENDPOINTS"
test_endpoint "Anatomy Overview" "GET" "$BASE_URL/anatomy" "" "200 422"
test_endpoint "Body Part Timeline" "GET" "$BASE_URL/anatomy/heart/timeline" "" "200 404 422"

echo -e "\n📋 EVENTS ENDPOINTS"
test_endpoint "Get Events" "GET" "$BASE_URL/events?user_id=$TEST_USER_ID" "" "200 422"
create_event_data="{\"type\":\"test\",\"description\":\"Test event\",\"date\":\"2024-01-01T12:00:00\",\"severity\":\"low\"}"
test_endpoint "Create Event" "POST" "$BASE_URL/events" "$create_event_data" "200 422"

# Cleanup
rm -f /tmp/test_doc.txt

echo -e "\n============================================================="
echo "🎯 TESTING COMPLETE"
echo "============================================================="
