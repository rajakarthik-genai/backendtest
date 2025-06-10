"""
Long-term memory (LTM) – per-user persistent profile / medical summary.

Backed by Redis for low-latency reads by agents during prompt construction.
"""

import json
from typing import Dict, Any
from urllib.parse import urlparse
import redis
from src.config.settings import settings
from src.utils.logging import logger

# Convert settings.redis_url to str before parsing
parsed = urlparse(str(settings.redis_url))
redis_client = redis.Redis(
    host=parsed.hostname,
    port=parsed.port,
    db=int(parsed.path.lstrip("/")) if parsed.path.lstrip("/") else 0,
    decode_responses=True
)


class LongTermMemory:
    """Static helpers for CRUD on `ltm:<user_id>` keys."""

    @staticmethod
    def get(user_id: str) -> Dict[str, Any]:
        data = redis_client.get(f"ltm:{user_id}")
        return json.loads(data) if data else {}

    @staticmethod
    def update(user_id: str, new: Dict[str, Any]) -> None:
        """
        Merge *new* into existing LTM without losing prior keys.
        List-valued fields are merged by set union to avoid duplicates.
        """
        current = LongTermMemory.get(user_id)
        for k, v in new.items():
            if isinstance(v, list):
                cur = set(current.get(k, []))
                cur.update(v)
                current[k] = list(cur)
            else:
                current[k] = v
        redis_client.set(f"ltm:{user_id}", json.dumps(current))
        logger.debug("LTM updated for %s – keys=%s", user_id, list(new))
