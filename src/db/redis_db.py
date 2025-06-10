# File: db/redis_db.py
import os
import json
import logging
import redis
from src.config.settings import settings

logger = logging.getLogger("memory.redis")

class _Stub:
    def set(self, *_, **__): pass
    def get(self, *_): return None
    def delete(self, *_): pass
    def rpush(self, *_, **__): pass
    def ltrim(self, *_, **__): pass
    def lrange(self, *_, **__): return []
    def expire(self, *_, **__): pass
    def ping(self): return False

def _dumps(o):
    return json.dumps(o, default=str)

def _loads(s):
    if s is None:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return s

try:
    _client = redis.Redis(
        host=settings.redis_host,  # lower-case attribute from Settings
        port=settings.redis_port
    )
    _client.ping()
    logger.info("Connected to Redis @ %s", settings.redis_url)
except Exception as exc:
    logger.warning("Redis unavailable (%s) — falling back to stub", exc)
    _client = _Stub()

# Re-export helpers for other modules with the desired alias.
client  = _client
dumps   = _dumps
loads   = _loads

redis_client = client

class RedisDB:
    """
    Redis client for caching and managing chat memory.
    """
    def __init__(self, host="localhost", port=6379, db=0):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,  # should resolve to "redis" from .env
            port=settings.REDIS_PORT,
            db=db, decode_responses=True
        )

    def set(self, key, value, ex=None):
        """
        Cache a value (as JSON) with an optional expiry (in seconds).
        """
        self.client.set(key, json.dumps(value), ex=ex)

    def get(self, key):
        """
        Retrieve a cached value by key.
        """
        val = self.client.get(key)
        if val:
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return val
        return None

    # Chat memory functions
    def add_chat_message(self, session_id, sender, text):
        """
        Append a chat message (with sender and text) to the session's history list.
        """
        key = f"chat:{session_id}"
        message = {
            "sender": sender,
            "text": text,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        # Use RPUSH to add message to the end of list
        self.client.rpush(key, json.dumps(message))

    def get_chat_history(self, session_id, count=20):
        """
        Retrieve the last `count` messages from a chat session.
        """
        key = f"chat:{session_id}"
        raw_msgs = self.client.lrange(key, -count, -1)
        history = []
        for raw in raw_msgs:
            try:
                history.append(json.loads(raw))
            except json.JSONDecodeError:
                history.append(raw)
        return history
