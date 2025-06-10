"""
/chat/expert_opinion – explicitly call multi-specialist panel and aggregator.
"""

from uuid import uuid4
from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import JSONResponse
from src.agents.expert_router import choose_specialists, get_handlers
from src.agents.aggregation_agent import aggregate
from src.chat.history import ChatHistory as Hist
from src.utils.logging import logger

router = APIRouter(prefix="/chat", tags=["expert-opinion"])


@router.post("/expert_opinion")
async def expert_opinion(
    request: Request,
    user_id: str = Query(...),
    conv_id: str | None = Query(None),
):
    data = await request.json()
    question = data.get("message")
    if not question:
        raise HTTPException(400, detail="`message` is required")
    conv_id = conv_id or str(uuid4())
    Hist.add_msg(user_id, "expert_panel", conv_id, "user", question)

    # choose specialists & collect answers
    roles = choose_specialists(question)
    answers = []
    for role, handler in zip(roles, get_handlers(roles)):
        try:
            ans = handler(user_id, question)
            answers.append(f"{role.title()}:\n{ans}")
        except Exception as exc:
            answers.append(f"{role.title()} failed: {exc}")
    final_answer = aggregate(question, answers)
    Hist.add_msg(user_id, "expert_panel", conv_id, "assistant", final_answer)
    logger.info("Expert opinion delivered for user %s conv %s", user_id, conv_id)
    return JSONResponse({"conversation_id": conv_id, "answer": final_answer})
