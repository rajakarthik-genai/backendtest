"""
Thread-safe Redis singleton with graceful No-Op fallback.

If $REDIS_URL is undefined or the server is unreachable,
we replace the client with a stub that does nothing—
the rest of the backend continues to run (dev-friendly).
"""
import os, json, logging
import redis
logger = logging.getLogger("memory.redis")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class _Stub:
    def set(self, *_, **__): pass
    def get(self, *_): return None
    def delete(self, *_): pass
    def rpush(self, *_, **__): pass
    def ltrim(self, *_, **__): pass
    def lrange(self, *_, **__): return []
    def expire(self, *_, **__): pass
    def ping(self): return False

def _dumps(o): return json.dumps(o, default=str)
def _loads(s):  # returns raw string if not json
    if s is None: return None
    try: return json.loads(s)
    except json.JSONDecodeError: return s

try:
    _client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    _client.ping()
    logger.info("Connected to Redis @ %s", REDIS_URL)
except Exception as exc:                   # pragma: no cover
    logger.warning("Redis unavailable (%s) — falling back to stub", exc)
    _client = _Stub()

# re-export helpers for other modules
client  = _client
dumps   = _dumps
loads   = _loads
