"""
Redis database for chat history, session management, and caching.

Handles:
- Short-term chat memory
- Session state management
- Temporary data caching
- User data isolation via key prefixing
"""

import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from src.config.settings import settings
from src.utils.logging import logger


class RedisDB:
    """Redis database manager for caching and session management."""
    
    def __init__(self):
        self.client = None
        self._initialized = False
    
    def initialize(self, host: str, port: int, db: int = 0):
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using fallback")
            self.client = MockRedis()
            self._initialized = True
            return
        
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self.client.ping()
            
            self._initialized = True
            logger.info(f"Redis connected to {host}:{port}")
            
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            # Use mock Redis as fallback
            self.client = MockRedis()
            self._initialized = True
    
    def _hash_user_id(self, user_id: str, secret_key: str = None) -> str:
        """Create consistent hash of user_id for data isolation."""
        if not secret_key:
            secret_key = settings.redis_host
        
        return hmac.new(
            secret_key.encode(),
            user_id.encode(),
            hashlib.sha256
        ).hexdigest()[:16]  # Shorter hash for Redis keys
    
    def _get_user_key(self, user_id: str, key_suffix: str) -> str:
        """Generate user-specific key with isolation."""
        hashed_user_id = self._hash_user_id(user_id)
        return f"user:{hashed_user_id}:{key_suffix}"
    
    def store_chat_message(
        self,
        user_id: str,
        session_id: str,
        message: Dict[str, Any],
        ttl_hours: int = 24
    ) -> bool:
        """Store a chat message in user's session history."""
        if not self._initialized:
            raise RuntimeError("Redis not initialized")
        
        try:
            key = self._get_user_key(user_id, f"chat:{session_id}")
            
            # Add timestamp to message
            message_data = {
                **message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store as list (append to conversation)
            self.client.lpush(key, json.dumps(message_data, default=str))
            
            # Set expiration
            self.client.expire(key, ttl_hours * 3600)
            
            # Limit conversation length (keep last 100 messages)
            self.client.ltrim(key, 0, 99)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store chat message: {e}")
            return False
    
    def get_chat_history(
        self,
        user_id: str,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieve chat history for a user session."""
        if not self._initialized:
            raise RuntimeError("Redis not initialized")
        
        try:
            key = self._get_user_key(user_id, f"chat:{session_id}")
            
            # Get messages (most recent first)
            messages = self.client.lrange(key, 0, limit - 1)
            
            chat_history = []
            for msg in reversed(messages):  # Reverse to get chronological order
                try:
                    chat_history.append(json.loads(msg))
                except json.JSONDecodeError:
                    continue
            
            return chat_history
            
        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            return []
    
    def store_session_data(
        self,
        user_id: str,
        session_id: str,
        data: Dict[str, Any],
        ttl_hours: int = 12
    ) -> bool:
        """Store session-specific data."""
        if not self._initialized:
            raise RuntimeError("Redis not initialized")
        
        try:
            key = self._get_user_key(user_id, f"session:{session_id}")
            
            session_data = {
                **data,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            self.client.setex(
                key,
                ttl_hours * 3600,
                json.dumps(session_data, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store session data: {e}")
            return False
    
    def get_session_data(
        self,
        user_id: str,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve session data."""
        if not self._initialized:
            raise RuntimeError("Redis not initialized")
        
        try:
            key = self._get_user_key(user_id, f"session:{session_id}")
            data = self.client.get(key)
            
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get session data: {e}")
            return None
    
    def cache_data(
        self,
        cache_key: str,
        data: Any,
        ttl_seconds: int = 3600
    ) -> bool:
        """Cache arbitrary data with TTL."""
        if not self._initialized:
            raise RuntimeError("Redis not initialized")
        
        try:
            self.client.setex(
                f"cache:{cache_key}",
                ttl_seconds,
                json.dumps(data, default=str)
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache data: {e}")
            return False
    
    def get_cached_data(self, cache_key: str) -> Any:
        """Retrieve cached data."""
        if not self._initialized:
            raise RuntimeError("Redis not initialized")
        
        try:
            data = self.client.get(f"cache:{cache_key}")
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached data: {e}")
            return None
    
    def store_processing_status(
        self,
        task_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
        ttl_hours: int = 24
    ) -> bool:
        """Store task processing status."""
        if not self._initialized:
            raise RuntimeError("Redis not initialized")
        
        try:
            status_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            self.client.setex(
                f"task:{task_id}",
                ttl_hours * 3600,
                json.dumps(status_data, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store processing status: {e}")
            return False
    
    def get_processing_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task processing status."""
        if not self._initialized:
            raise RuntimeError("Redis not initialized")
        
        try:
            data = self.client.get(f"task:{task_id}")
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get processing status: {e}")
            return None
    
    def delete_user_data(self, user_id: str) -> bool:
        """Delete all data for a specific user."""
        if not self._initialized:
            raise RuntimeError("Redis not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            pattern = f"user:{hashed_user_id}:*"
            
            # Find all keys matching the pattern
            keys = self.client.keys(pattern)
            
            if keys:
                self.client.delete(*keys)
            
            logger.info(f"Deleted {len(keys)} keys for user {user_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user data: {e}")
            return False
    
    def close(self):
        """Close Redis connection."""
        if self.client and hasattr(self.client, 'close'):
            self.client.close()
            logger.info("Redis connection closed")


class MockRedis:
    """Mock Redis implementation for fallback."""
    
    def __init__(self):
        self.data = {}
        self.expiry = {}
    
    def ping(self):
        return True
    
    def setex(self, key: str, ttl: int, value: str):
        self.data[key] = value
        self.expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)
    
    def get(self, key: str) -> Optional[str]:
        if key in self.expiry and datetime.utcnow() > self.expiry[key]:
            self.delete(key)
            return None
        return self.data.get(key)
    
    def lpush(self, key: str, value: str):
        if key not in self.data:
            self.data[key] = []
        self.data[key].insert(0, value)
    
    def lrange(self, key: str, start: int, end: int) -> List[str]:
        if key not in self.data:
            return []
        return self.data[key][start:end + 1]
    
    def ltrim(self, key: str, start: int, end: int):
        if key in self.data:
            self.data[key] = self.data[key][start:end + 1]
    
    def expire(self, key: str, ttl: int):
        self.expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)
    
    def delete(self, *keys):
        for key in keys:
            self.data.pop(key, None)
            self.expiry.pop(key, None)
    
    def keys(self, pattern: str) -> List[str]:
        # Simple pattern matching
        if pattern.endswith('*'):
            prefix = pattern[:-1]
            return [k for k in self.data.keys() if k.startswith(prefix)]
        return [pattern] if pattern in self.data else []
    
    def close(self):
        pass


# Global Redis instance
redis_db = RedisDB()


def init_redis(host: str, port: int, db: int = 0):
    """Initialize global Redis instance."""
    redis_db.initialize(host, port, db)


def get_redis() -> RedisDB:
    """Get Redis instance."""
    if not redis_db._initialized:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return redis_db
