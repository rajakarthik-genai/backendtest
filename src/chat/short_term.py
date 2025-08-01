"""
Short-term memory (STM) – per-conversation rolling context.

Each chat session is keyed:

    stm:<user_id>:<doctor_id>:<conv_id>

Stored as a Redis list of JSON messages.
"""

import json
from datetime import datetime
from typing import List, Dict, Any
from src.db.redis_db import get_redis
from src.utils.logging import logger

_MAX_CTX = 20  # keep last N messages for context


class ShortTermMemory:
    """STM helper utilities with both static and instance methods."""

    def __init__(self):
        """Initialize ShortTermMemory instance."""
        pass

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

    # Instance methods for chat router compatibility
    async def get_recent_messages(self, patient_id: str, limit: int = 20, conversation_id: str = "default") -> List[Dict]:
        """
        Get recent messages for a patient.
        
        Args:
            patient_id: Patient identifier
            limit: Maximum number of messages to return
            conversation_id: Conversation identifier (defaults to "default")
            
        Returns:
            List of recent messages
        """
        try:
            redis_client = get_redis()
            messages = redis_client.get_chat_history(patient_id, conversation_id)
            
            # Return the most recent messages up to the limit
            return messages[-limit:] if messages else []
            
        except Exception as e:
            logger.error(f"Failed to get recent messages for patient {patient_id}: {e}")
            return []

    async def store_message(
        self,
        patient_id: str,
        conversation_id: str,
        user_message: str = None,
        assistant_message: str = None,
        metadata: Dict = None,
        timestamp: str = None
    ) -> bool:
        """
        Store a message in short-term memory.
        
        Args:
            patient_id: Patient identifier
            conversation_id: Conversation identifier
            user_message: User message content
            assistant_message: Assistant message content
            metadata: Additional message metadata
            timestamp: Optional timestamp (ignored, uses current time)
            
        Returns:
            Success status
        """
        try:
            redis_client = get_redis()
            
            # Store user message if provided
            if user_message:
                user_data = {
                    "role": "user",
                    "content": user_message,
                    "timestamp": str(datetime.now()),
                }
                if metadata:
                    user_data.update(metadata)
                redis_client.store_chat_message(patient_id, conversation_id, user_data)
            
            # Store assistant message if provided
            if assistant_message:
                assistant_data = {
                    "role": "assistant", 
                    "content": assistant_message,
                    "timestamp": str(datetime.now()),
                }
                if metadata:
                    assistant_data.update(metadata)
                redis_client.store_chat_message(patient_id, conversation_id, assistant_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store message for patient {patient_id}: {e}")
            return False

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
def get_short_term_memory():
    """Get short-term memory instance."""
    return ShortTermMemory()
