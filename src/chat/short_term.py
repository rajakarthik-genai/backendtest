"""
Short-term memory (STM) – per-conversation rolling context.

Each chat session is keyed:

    stm:<user_id>:<doctor_id>:<conv_id>

Stored as a Redis list of JSON messages.
"""

import json
from typing import List, Dict, Any
from src.db.redis_db import get_redis
from src.utils.logging import logger

_MAX_CTX = 20  # keep last N messages for context


class ShortTermMemory:
    """Static STM helper utilities."""

    @staticmethod
    def _key(user: str, doctor: str, conv: str) -> str:
        return f"stm:{user}:{doctor}:{conv}"

    @staticmethod
    async def add(user: str, doctor: str, conv: str, role: str, content: str) -> None:
        try:
            redis_client = get_redis()
            entry = json.dumps({"role": role, "content": content})
            
            # Use store_chat_message method from RedisDB
            message_data = {"role": role, "content": content}
            redis_client.store_chat_message(user, conv, message_data)
            
        except Exception as e:
            logger.error(f"Failed to add STM message: {e}")

    @staticmethod
    async def history(user: str, doctor: str, conv: str) -> List[Dict]:
        try:
            redis_client = get_redis()
            # Use get_chat_history method from RedisDB
            messages = redis_client.get_chat_history(user, conv)
            return messages
        except Exception as e:
            logger.error(f"Failed to get STM history: {e}")
            return []

    @staticmethod
    async def last_user_msg(user: str, doctor: str, conv: str) -> str | None:
        try:
            history = await ShortTermMemory.history(user, doctor, conv)
            for msg in reversed(history):
                if msg.get("role") == "user":
                    return msg.get("content")
            return None
        except Exception as e:
            logger.error(f"Failed to get last user message: {e}")
            return None

    @staticmethod
    async def clear(user: str, doctor: str, conv: str) -> None:
        try:
            redis_client = get_redis()
            # Use delete_user_data or a similar method
            key = ShortTermMemory._key(user, doctor, conv)
            redis_client.client.delete(key)
            logger.debug("STM cleared for conv %s", conv)
        except Exception as e:
            logger.error(f"Failed to clear STM: {e}")

    @staticmethod
    async def get_context(user_id: str, session_id: str, doctor_id: str = "default") -> Dict[str, Any]:
        """Get short-term memory context for a user session."""
        # Retrieve full history and last user message
        history = await ShortTermMemory.history(user_id, doctor_id, session_id)
        last_msg = await ShortTermMemory.last_user_msg(user_id, doctor_id, session_id)
        return {
            "recent_messages": history,
            "last_user_message": last_msg,
            "message_count": len(history)
        }


# Factory function for compatibility
async def get_short_term_memory():
    """Get short-term memory instance."""
    return ShortTermMemory
