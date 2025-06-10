"""
/chat/stream – realtime chat with a doctor agent (or orchestrator)
"""

from uuid import uuid4
from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import EventSourceResponse
from src.agents.orchestrator_agent import orchestrator_agent
from src.chat.history import ChatHistory as Hist
from src.utils.logging import logger

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
async def stream_chat(
    request: Request,
    user_id: str = Query(...),
    doctor_id: str = Query("gp"),  # default doctor id (general physician)
    conv_id: str | None = Query(None),
):
    """
    Open SSE stream: send {"message":"..."} in body, receive incremental chunks.
    """
    data = await request.json()
    question = data.get("message")
    if not question:
        raise HTTPException(400, detail="`message` is required")
    conv_id = conv_id or str(uuid4())
    # Save user message
    Hist.add_msg(user_id, doctor_id, conv_id, "user", question)

    async def event_stream():
        async for chunk in orchestrator_agent.handle_request(
            user_id=user_id,
            doctor_id=doctor_id,
            conv_id=conv_id,
            user_msg=question,
        ):
            yield chunk
        yield "data: [DONE]\n\n"

    logger.info("SSE started for conv=%s user=%s", conv_id, user_id)
    return EventSourceResponse(event_stream(), media_type="text/event-stream")
