"""
Long-term memory (LTM) – per-user persistent profile / medical summary.

Backed by Redis for low-latency reads by agents during prompt construction.
"""

import json
from typing import Dict, Any
from src.db.redis_db import get_redis
from src.utils.logging import logger


class LongTermMemory:
    """Static helpers for CRUD on `ltm:<user_id>` keys."""

    @staticmethod
    async def get(user_id: str) -> Dict[str, Any]:
        try:
            redis_client = get_redis()
            data = redis_client.client.get(f"ltm:{user_id}")
            return json.loads(data) if data else {}
        except Exception as e:
            logger.error(f"Failed to get LTM for user {user_id}: {e}")
            return {}

    @staticmethod
    async def update(user_id: str, new: Dict[str, Any]) -> None:
        """
        Merge *new* into existing LTM without losing prior keys.
        List-valued fields are merged by set union to avoid duplicates.
        """
        try:
            current = await LongTermMemory.get(user_id)
            for k, v in new.items():
                if isinstance(v, list):
                    cur = set(current.get(k, []))
                    cur.update(v)
                    current[k] = list(cur)
                else:
                    current[k] = v
            
            redis_client = get_redis()
            redis_client.client.set(f"ltm:{user_id}", json.dumps(current))
            logger.debug("LTM updated for %s – keys=%s", user_id, list(new.keys()))
        except Exception as e:
            logger.error(f"Failed to update LTM for user {user_id}: {e}")

    @staticmethod
    async def get_user_context(user_id: str) -> Dict[str, Any]:
        """Get user context from long-term memory."""
        data = await LongTermMemory.get(user_id)
        return {
            "user_profile": data.get("profile", {}),
            "medical_history": data.get("medical_history", []),
            "preferences": data.get("preferences", {}),
            "conversation_patterns": data.get("conversation_patterns", {})
        }


# Factory function for compatibility
async def get_long_term_memory():
    """Get long-term memory instance."""
    return LongTermMemory
