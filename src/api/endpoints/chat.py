# api/endpoints/chat.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime
import json
import openai
from pymongo import MongoClient
from chat.long_term import get_long_term_memory, update_long_term_memory
from chat.short_term import add_message_to_stm, get_short_term_memory

router = APIRouter(prefix="/chat")

# Initialize MongoDB (synchronous for simplicity)
mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client["chat_db"]
messages_col = db["messages"]

# Example OpenAI API key setup (assumes env var or config)
openai.api_key = "YOUR_OPENAI_KEY"  

class ChatRequest(BaseModel):
    user_id: str
    doctor_id: str
    conversation_id: str
    message: str

@router.post("/stream")
async def chat_stream(req: ChatRequest):
    user_id = req.user_id
    doctor_id = req.doctor_id
    conv_id = req.conversation_id
    user_msg = req.message

    # 1) Store the user message in short-term memory and Mongo
    add_message_to_stm(user_id, doctor_id, conv_id, "user", user_msg)
    messages_col.insert_one({
        "user_id": user_id,
        "doctor_id": doctor_id,
        "conversation_id": conv_id,
        "role": "user",
        "content": user_msg,
        "timestamp": datetime.utcnow()
    })

    # 2) Retrieve long-term memory and prepare the prompt
    ltm = get_long_term_memory(user_id)
    history = get_short_term_memory(user_id, doctor_id, conv_id)
    messages = []
    if ltm:
        # Provide memory as system context (could be more elaborate)
        messages.append({
            "role": "system",
            "content": f"Patient medical history: {json.dumps(ltm)}"
        })
    # Include recent history (which now contains the just-added user message and prior turns)
    messages.extend(history)

    # 3) Define a generator to stream the OpenAI response
    def event_stream():
        # Call the OpenAI ChatCompletion with streaming
        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=messages,
            stream=True,
            functions=[
                {
                    "name": "update_memory",
                    "description": "Update patient history in JSON format",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "conditions": {"type": "array", "items": {"type": "string"}},
                            "lab_anomalies": {"type": "array", "items": {"type": "string"}},
                            "injuries": {"type": "array", "items": {"type": "string"}},
                            "allergies": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                }
            ],
        )
        assistant_text = ""
        # Stream the response chunks
        for chunk in response:
            # Extract any new text from the assistant
            delta = chunk["choices"][0]["delta"].get("content")
            if delta:
                assistant_text += delta
                # Yield as SSE data message
                yield f"data: {delta}\n\n"
        # After streaming is complete:
        # Save the assistant message to short-term memory and Mongo
        if assistant_text:
            add_message_to_stm(user_id, doctor_id, conv_id, "assistant", assistant_text)
            messages_col.insert_one({
                "user_id": user_id,
                "doctor_id": doctor_id,
                "conversation_id": conv_id,
                "role": "assistant",
                "content": assistant_text,
                "timestamp": datetime.utcnow()
            })
        # 4) Update long-term memory using a function call
        try:
            # Call the model again to extract memory updates (non-streaming for simplicity)
            mem_response = openai.ChatCompletion.create(
                model="gpt-4-0613",
                messages=[
                    {"role": "system", "content": "Based on the conversation, update the patient's medical history. Output JSON with keys: conditions, lab_anomalies, injuries, allergies."},
                    {"role": "assistant", "content": assistant_text}
                ],
                functions=[response.request.kwargs["functions"][0]],
                function_call={"name": "update_memory"}
            )
            # Parse function arguments as JSON
            mem_args = mem_response["choices"][0]["message"]["function_call"]["arguments"]
            new_memory = json.loads(mem_args)
            update_long_term_memory(user_id, new_memory)
        except Exception as e:
            # If memory update fails, skip
            pass

    # Return streaming response (SSE)
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.get("/conversations")
async def list_conversations(user_id: str = Query(...), doctor_id: str = Query(...)):
    """
    List all conversation IDs for the given user and doctor.
    """
    conv_ids = messages_col.distinct(
        "conversation_id",
        {"user_id": user_id, "doctor_id": doctor_id}
    )
    return {"conversations": conv_ids}

@router.get("/history/{conversation_id}")
async def get_history(conversation_id: str, skip: int = 0, limit: int = 50):
    """
    Get paginated message history for a conversation ID.
    """
    cursor = messages_col.find(
        {"conversation_id": conversation_id}
    ).sort("timestamp", 1).skip(skip).limit(limit)
    history = []
    for msg in cursor:
        history.append({
            "role": msg["role"],
            "content": msg["content"],
            "timestamp": msg["timestamp"]
        })
    return {"messages": history}

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete all messages for a given conversation.
    """
    result = messages_col.delete_many({"conversation_id": conversation_id})
    return {"deleted_count": result.deleted_count}
