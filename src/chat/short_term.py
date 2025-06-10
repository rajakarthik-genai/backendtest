"""
Short-term memory (STM) – per-conversation rolling context.

Each chat session is keyed:

    stm:<user_id>:<doctor_id>:<conv_id>

Stored as a Redis list of JSON messages.
"""

import json
from typing import List, Dict
import redis
from src.config.settings import settings
from src.utils.logging import logger

_MAX_CTX = 20  # keep last N messages for context

_redis = redis.Redis(
    host=settings.redis_url.hostname,
    port=settings.redis_url.port,
    db=0,
    decode_responses=True,
)


class ShortTermMemory:
    """Static STM helper utilities."""

    @staticmethod
    def _key(user: str, doctor: str, conv: str) -> str:
        return f"stm:{user}:{doctor}:{conv}"

    @staticmethod
    def add(user: str, doctor: str, conv: str, role: str, content: str) -> None:
        entry = json.dumps({"role": role, "content": content})
        _redis.rpush(ShortTermMemory._key(user, doctor, conv), entry)
        _redis.ltrim(ShortTermMemory._key(user, doctor, conv), -_MAX_CTX, -1)

    @staticmethod
    def history(user: str, doctor: str, conv: str) -> List[Dict]:
        raw = _redis.lrange(ShortTermMemory._key(user, doctor, conv), 0, -1)
        return [json.loads(m) for m in raw]

    @staticmethod
    def last_user_msg(user: str, doctor: str, conv: str) -> str | None:
        for msg in reversed(ShortTermMemory.history(user, doctor, conv)):
            if msg["role"] == "user":
                return msg["content"]
        return None

    @staticmethod
    def clear(user: str, doctor: str, conv: str) -> None:
        _redis.delete(ShortTermMemory._key(user, doctor, conv))
        logger.debug("STM cleared for conv %s", conv)
