#!/usr/bin/env python3
"""
Test script for the new conversation endpoints
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"  # Adjust as needed
API_KEY = "your_api_key_here"  # You'll need to provide a valid token

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

async def test_conversation_flow():
    """Test the complete conversation flow"""
    async with aiohttp.ClientSession() as session:
        
        print("🧪 Testing Conversation Endpoints")
        print("=" * 50)
        
        # Test 1: Create new conversation (GET)
        print("\n1. Creating new conversation (GET /chat/conversations/new)")
        async with session.get(f"{BASE_URL}/chat/conversations/new", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                conversation_id = data["data"]["conversation_id"]
                print(f"✅ Created conversation: {conversation_id}")
                print(f"   Remaining messages: {data['data']['remaining_messages']}")
            else:
                print(f"❌ Failed to create conversation: {response.status}")
                text = await response.text()
                print(f"   Error: {text}")
                return
        
        # Test 2: Add first message (POST)
        print(f"\n2. Adding first message (POST /chat/conversations/new)")
        first_message = {
            "conversation_id": conversation_id,
            "message": "I have been experiencing chest pain and shortness of breath. What could be the cause?",
            "role": "user"
        }
        
        async with session.post(f"{BASE_URL}/chat/conversations/new", 
                              headers=headers, 
                              json=first_message) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Added first message")
                print(f"   Remaining messages: {data['data']['remaining_messages']}")
                if data['data'].get('warning'):
                    print(f"   Warning: {data['data']['warning']}")
            else:
                print(f"❌ Failed to add message: {response.status}")
                text = await response.text()
                print(f"   Error: {text}")
                return
        
        # Wait a bit for title generation
        print("\n   Waiting for title generation...")
        await asyncio.sleep(2)
        
        # Test 3: Add assistant response
        print(f"\n3. Adding assistant response")
        assistant_message = {
            "conversation_id": conversation_id,
            "message": "Chest pain and shortness of breath can have various causes. Common possibilities include cardiovascular issues, respiratory problems, or anxiety. I recommend consulting with a healthcare professional for proper evaluation and diagnosis.",
            "role": "assistant"
        }
        
        async with session.post(f"{BASE_URL}/chat/conversations/new", 
                              headers=headers, 
                              json=assistant_message) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Added assistant response")
                print(f"   Remaining messages: {data['data']['remaining_messages']}")
            else:
                print(f"❌ Failed to add assistant message: {response.status}")
                text = await response.text()
                print(f"   Error: {text}")
        
        # Test 4: List conversations to see if title was generated
        print(f"\n4. Listing conversations (GET /chat/conversations)")
        async with session.get(f"{BASE_URL}/chat/conversations", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                conversations = data["data"]["conversations"]
                print(f"✅ Found {len(conversations)} conversations")
                
                for conv in conversations:
                    if conv["conversation_id"] == conversation_id:
                        print(f"   📝 Title: '{conv['title']}'")
                        print(f"   📅 Created: {conv['created_at']}")
                        print(f"   💬 Messages: {conv['message_count']}")
                        print(f"   🔄 Updated: {conv['updated_at']}")
                        break
                else:
                    print(f"   ⚠️  Conversation {conversation_id} not found in list")
            else:
                print(f"❌ Failed to list conversations: {response.status}")
                text = await response.text()
                print(f"   Error: {text}")
        
        # Test 5: Get conversation history
        print(f"\n5. Getting conversation history")
        async with session.get(f"{BASE_URL}/chat/conversation/{conversation_id}/history", 
                             headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Retrieved conversation history")
                print(f"   Messages in history: {len(data.get('data', {}).get('messages', []))}")
            else:
                print(f"❌ Failed to get history: {response.status}")
                text = await response.text()
                print(f"   Error: {text}")
        
        print("\n" + "=" * 50)
        print("🎉 Test completed!")
        
        return conversation_id


async def test_multiple_conversations():
    """Test creating multiple conversations to verify title generation"""
    async with aiohttp.ClientSession() as session:
        
        print("\n\n🔄 Testing Multiple Conversations")
        print("=" * 50)
        
        test_messages = [
            "I have a persistent headache for the past week",
            "My blood pressure readings have been high lately",
            "I'm experiencing joint pain in my knees",
            "I have trouble sleeping and feel anxious"
        ]
        
        conversation_ids = []
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n{i}. Creating conversation and adding message: '{message[:40]}...'")
            
            # Create conversation
            async with session.get(f"{BASE_URL}/chat/conversations/new", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    conversation_id = data["data"]["conversation_id"]
                    conversation_ids.append(conversation_id)
                    
                    # Add message
                    msg_data = {
                        "conversation_id": conversation_id,
                        "message": message,
                        "role": "user"
                    }
                    
                    async with session.post(f"{BASE_URL}/chat/conversations/new", 
                                          headers=headers, json=msg_data) as msg_response:
                        if msg_response.status == 200:
                            print(f"   ✅ Created conversation: {conversation_id[:8]}...")
                        else:
                            print(f"   ❌ Failed to add message")
                else:
                    print(f"   ❌ Failed to create conversation")
        
        # Wait for title generation
        print("\n   Waiting for title generation...")
        await asyncio.sleep(3)
        
        # List all conversations to see titles
        print(f"\n📋 Final conversation list:")
        async with session.get(f"{BASE_URL}/chat/conversations", headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                conversations = data["data"]["conversations"]
                
                for conv in conversations:
                    if conv["conversation_id"] in conversation_ids:
                        print(f"   🆔 {conv['conversation_id'][:8]}... | 📝 '{conv['title']}' | 💬 {conv['message_count']} msgs")
            else:
                print(f"   ❌ Failed to list conversations")


if __name__ == "__main__":
    print("🚀 Starting Conversation Endpoint Tests")
    print("Please ensure the server is running and update the API_KEY variable")
    
    # Note: You'll need to get a valid JWT token for testing
    # You can run: python get_token.py or similar to get one
    
    asyncio.run(test_conversation_flow())
    asyncio.run(test_multiple_conversations())
