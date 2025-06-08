import json
import redis
from src.config.settings import settings

redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)

MAX_CTX = 20  # keep last 20 messages for context

def add_message_to_stm(user_id: str, doctor_id: str, conv_id: str, role: str, text: str) -> None:
    """Append a message to the short-term memory list (role is 'user' or 'assistant')."""
    key = f"stm:{user_id}:{doctor_id}:{conv_id}"
    entry = json.dumps({"role": role, "content": text})
    redis_client.rpush(key, entry)
    # Trim to last MAX_CTX entries to bound memory size
    redis_client.ltrim(key, -MAX_CTX, -1)

def get_short_term_memory(user_id: str, doctor_id: str, conv_id: str) -> list:
    """Retrieve the list of recent messages (as dicts) for the session, in chronological order."""
    key = f"stm:{user_id}:{doctor_id}:{conv_id}"
    items = redis_client.lrange(key, 0, -1)
    return [json.loads(item) for item in items]

def clear_short_term_memory(user_id: str, doctor_id: str, conv_id: str) -> None:
    """Clear the short-term memory for this conversation session."""
    key = f"stm:{user_id}:{doctor_id}:{conv_id}"
    redis_client.delete(key)
