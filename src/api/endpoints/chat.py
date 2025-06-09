"""
Chat streaming + CRUD endpoints.

•  POST /chat/stream            –  bidirectional SSE (OpenAI-style chunks)
•  GET  /chat/conversations     –  list conv-ids for user+doctor
•  GET  /chat/history/{conv_id} –  paginated messages
•  DELETE /chat/{conv_id}       –  delete conversation
"""
from uuid import uuid4
from typing import List

from fastapi import APIRouter, Request, Query, HTTPException, status
from fastapi.responses import EventSourceResponse, JSONResponse

from src.chat.short_term import add_message_to_stm
from src.db import mongo_db
from src.agents.orchestrator_agent import orchestrate  # CrewAI
from src.utils.logging import log

router = APIRouter(prefix="/chat", tags=["chat"])


# ─────────────────────────── Streaming chat ────────────────────────────────
@router.post("/stream")
async def chat_stream(
    request: Request,
    user_id: str = Query(...),
    doctor_id: str = Query(...),
    conv_id: str | None = Query(default=None),
):
    data = await request.json()
    question: str = data.get("message")
    if not question:
        raise HTTPException(400, "message is required")

    conv_id = conv_id or str(uuid4())
    add_message_to_stm(user_id, doctor_id, conv_id, "user", question)

    async def event_stream():
        async for delta in orchestrate(
            user_id=user_id,
            doctor_id=doctor_id,
            conv_id=conv_id,
            question=question,
        ):
            yield {"data": {"choices": [{"delta": {"content": delta}}]}}
        yield {"data": "[DONE]"}

    return EventSourceResponse(event_stream(), media_type="text/event-stream")


# ─────────────────────────── CRUD helpers ──────────────────────────────────
@router.get("/conversations")
async def list_conversations(
    user_id: str = Query(...), doctor_id: str = Query(...)
) -> List[str]:
    """Return list of conversation ids (latest first)."""
    pipeline = [
        {"$match": {"user_id": user_id, "doctor_id": doctor_id}},
        {"$group": {"_id": "$conv_id", "ts": {"$max": "$ts"}}},
        {"$sort": {"ts": -1}},
        {"$project": {"_id": 0, "conv_id": "$_id"}},
    ]
    convs = [d["conv_id"] for d in mongo_db.chat_col.aggregate(pipeline)]
    return convs


@router.get("/history/{conv_id}")
async def get_history(
    conv_id: str, skip: int = 0, limit: int = 50
) -> list[dict]:
    """Paginated chat history."""
    return [doc async for doc in mongo_db.get_chat_history(conv_id, skip, limit)]


@router.delete("/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conv_id: str):
    """Hard-delete one conversation (all messages)."""
    mongo_db.chat_col.delete_many({"conv_id": conv_id})
    return JSONResponse(status_code=204)
