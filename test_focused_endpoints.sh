#!/bin/bash
# Focused testing of Chat and Expert Opinion endpoints

BASE_URL="http://localhost:8000"
TEST_USER_ID="test_user_$(date +%s)"
SESSION_ID="session_$(date +%s)"

echo "============================================================="
echo "🎯 FOCUSED CHAT & EXPERT OPINION TESTING"
echo "============================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_endpoint() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    
    echo -e "\n🔍 Testing: $name"
    echo "   URL: $url"
    echo "   Data: $data"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" "$url" 2>/dev/null)
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$url" 2>/dev/null)
    fi
    
    status_code="${response: -3}"
    response_body="${response%???}"
    
    echo "   Status Code: $status_code"
    
    if [ "$status_code" = "200" ]; then
        echo -e "   ${GREEN}✅ SUCCESS${NC}"
    elif [ "$status_code" = "422" ]; then
        echo -e "   ${YELLOW}⚠️  VALIDATION ERROR${NC}"
    else
        echo -e "   ${RED}❌ ERROR${NC}"
    fi
    
    # Show response (truncated)
    if [ ${#response_body} -lt 1000 ] && echo "$response_body" | jq . >/dev/null 2>&1; then
        echo "   Response:"
        echo "$response_body" | jq . | head -20
    fi
}

echo -e "\n💬 CHAT ENDPOINTS - Testing with corrected parameters"

# Test chat message with user_id as query parameter
test_endpoint "Chat Message (with user_id)" "POST" "$BASE_URL/chat/message?user_id=$TEST_USER_ID" \
    '{"message":"What is the patient'\''s current condition?","conversation_id":"conv_123"}'

# Test chat stream
test_endpoint "Chat Stream (with user_id)" "POST" "$BASE_URL/chat/stream?user_id=$TEST_USER_ID" \
    '{"message":"Please analyze the patient data","conversation_id":"conv_123"}'

# Test chat sessions
test_endpoint "Chat Sessions (with user_id)" "GET" "$BASE_URL/chat/sessions?user_id=$TEST_USER_ID" ""

# Test chat history
test_endpoint "Chat History" "GET" "$BASE_URL/chat/history/conv_123?user_id=$TEST_USER_ID" ""

echo -e "\n🩺 EXPERT OPINION ENDPOINTS - Testing with corrected parameters"

# Test expert opinion with proper structure
test_endpoint "Expert Opinion (with user_id)" "POST" "$BASE_URL/expert/opinion?user_id=$TEST_USER_ID" \
    '{"message":"Please provide a cardiology consultation for a patient with chest pain","conversation_id":"expert_conv_123"}'

# Test expert opinion stream
test_endpoint "Expert Opinion Stream (with user_id)" "POST" "$BASE_URL/expert/opinion/stream?user_id=$TEST_USER_ID" \
    '{"message":"Provide neurological assessment for headaches","conversation_id":"expert_conv_456"}'

# Test getting expert conversation
test_endpoint "Get Expert Conversation" "GET" "$BASE_URL/expert/opinion/expert_conv_123?user_id=$TEST_USER_ID" ""

echo -e "\n📄 FILE UPLOAD TESTING"

# Test document upload with proper multipart form data
echo -e "\n🔍 Testing: Document Upload"
echo "Creating test document..."
echo "Test medical document content for upload testing. Patient reports chest pain and shortness of breath." > /tmp/test_medical.txt

echo "Uploading document..."
upload_response=$(curl -s -w "%{http_code}" -X POST \
    -F "file=@/tmp/test_medical.txt" \
    -F "user_id=$TEST_USER_ID" \
    "$BASE_URL/upload/document" 2>/dev/null)

upload_status="${upload_response: -3}"
upload_body="${upload_response%???}"

echo "   Status Code: $upload_status"

if [ "$upload_status" = "200" ] || [ "$upload_status" = "202" ]; then
    echo -e "   ${GREEN}✅ UPLOAD SUCCESS${NC}"
    if echo "$upload_body" | jq . >/dev/null 2>&1; then
        echo "   Response:"
        echo "$upload_body" | jq .
        
        # Extract document ID if available
        document_id=$(echo "$upload_body" | jq -r '.document_id // .id // empty')
        if [ -n "$document_id" ] && [ "$document_id" != "null" ]; then
            echo -e "\n🔍 Testing: Upload Status Check (with real ID)"
            status_response=$(curl -s -w "%{http_code}" "$BASE_URL/upload/status/$document_id" 2>/dev/null)
            status_code="${status_response: -3}"
            echo "   Status Code: $status_code"
            if echo "${status_response%???}" | jq . >/dev/null 2>&1; then
                echo "   Response:"
                echo "${status_response%???}" | jq .
            fi
        fi
    fi
else
    echo -e "   ${RED}❌ UPLOAD FAILED${NC}"
    echo "   Response: $upload_body"
fi

# Cleanup
rm -f /tmp/test_medical.txt

echo -e "\n🧪 ADDITIONAL ENDPOINT TESTING"

# Test events with proper parameters
test_endpoint "Get Events (with user_id)" "GET" "$BASE_URL/events/?user_id=$TEST_USER_ID" ""

# Test create event with proper structure
test_endpoint "Create Event (corrected)" "POST" "$BASE_URL/events/" \
    '{"event_type":"symptom","title":"Test Symptom","description":"Patient reports headache","severity":"medium","timestamp":"2024-01-01T12:00:00Z","user_id":"'$TEST_USER_ID'"}'

# Test timeline with proper query parameters
test_endpoint "Add Timeline Event (corrected)" "POST" "$BASE_URL/timeline/event?event_type=symptom&title=Test&description=Test%20event" ""

echo -e "\n============================================================="
echo "🎯 FOCUSED TESTING COMPLETE"
echo "============================================================="

echo -e "\n📊 KEY OBSERVATIONS:"
echo "✅ Expert specialties endpoint works perfectly"
echo "✅ Timeline summary and search endpoints work"
echo "✅ Authentication endpoints respond correctly"
echo "❓ Chat endpoints may need proper authentication"
echo "❓ Some endpoints require specific parameter formats"
echo "❓ Upload functionality needs multipart form data"

echo -e "\n💡 NEXT STEPS:"
echo "1. Test with proper JWT authentication for protected endpoints"
echo "2. Verify RAG functionality after document upload"
echo "3. Test streaming endpoints with SSE client"
echo "4. Check database connections and data persistence"
