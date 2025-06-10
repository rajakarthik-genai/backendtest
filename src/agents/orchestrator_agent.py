"""
Main orchestrator agent: uses expert_router to pick specialists,
collects answers, then streams aggregated reply.
"""

from typing import Generator
import json, openai
from uuid import uuid4

from src.config.settings import settings
from src.memory.memory_manager import (
    add_message_to_history,
    get_conversation_history,
    get_long_term_memory,
)
from src.utils.logging import logger
from .expert_router import choose_specialists, get_handlers
from .aggregator_agent import aggregate_stream

openai.api_key = settings.openai_api_key


class OrchestratorAgent:
    """Delegate question to specialists and aggregate answers."""
    def __init__(self):
        self.model = settings.openai_model_chat

    async def handle_request(
        self,
        user_id: str,
        doctor_id: str,
        conv_id: str,
        user_msg: str,
    ) -> Generator[str, None, None]:
        """
        Yield SSE chunks of aggregated response.
        """
        # 0. Save user message in history
        add_message_to_history(user_id, doctor_id, conv_id, "user", user_msg)

        # 1. Decide specialists
        roles = choose_specialists(user_msg)
        handlers = get_handlers(roles)
        logger.info("Orchestrator selected specialists: %s", roles)

        # 2. Collect answers
        answers = []
        for role, handler in zip(roles, handlers):
            try:
                answer = handler(user_id, user_msg)
                answers.append(f"{role.title()}:\n{answer}")
            except Exception as exc:
                answers.append(f"{role.title()} failed: {exc}")

        # 3. Stream aggregated answer
        for chunk in aggregate_stream(user_msg, answers):
            yield chunk

        # 4. Store assistant message
        add_message_to_history(user_id, doctor_id, conv_id, "assistant", "(see stream)")

# singleton instance
orchestrator_agent = OrchestratorAgent()
