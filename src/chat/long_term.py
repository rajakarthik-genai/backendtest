import json
import redis
from src.config.settings import settings

redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True)

def get_long_term_memory(user_id: str) -> dict:
    """Retrieve the long-term memory JSON for a given user."""
    key = f"ltm:{user_id}"
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return {}

def update_long_term_memory(user_id: str, new_data: dict) -> None:
    """
    Merge new_data into the existing long-term memory for the user.
    Avoid duplicates (e.g. via set union) for list fields.
    """
    key = f"ltm:{user_id}"
    existing = get_long_term_memory(user_id)
    # Merge lists under each key, avoiding duplicates
    for field, values in new_data.items():
        if not isinstance(values, list):
            existing[field] = values
            continue
        existing_list = existing.get(field, [])
        # Combine unique entries
        merged = existing_list.copy()
        for item in values:
            if item not in merged:
                merged.append(item)
        existing[field] = merged
    # Save updated memory back to Redis
    redis_client.set(key, json.dumps(existing))

def clear_long_term_memory(user_id: str) -> None:
    """Clear the long-term memory for a user (optional)."""
    redis_client.delete(f"ltm:{user_id}")
