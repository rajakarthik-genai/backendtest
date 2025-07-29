"""
Redis connection and operations
"""

import logging
import json
import asyncio
from typing import Optional, Any, Dict, List
import redis.asyncio as redis
from redis.asyncio import Redis

from src.core.config import settings
from src.core.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client for caching and queue operations"""
    
    def __init__(self):
        self.client: Optional[Redis] = None
        self.connected = False
    
    @classmethod
    async def create(cls):
        """Create and connect Redis client"""
        instance = cls()
        await instance.connect()
        return instance
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self.client.ping()
            self.connected = True
            logger.info("Connected to Redis successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise DatabaseConnectionError(f"Redis connection failed: {str(e)}")
    
    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            self.connected = False
            logger.info("Redis connection closed")
    
    async def ping(self) -> bool:
        """Check if Redis is connected"""
        try:
            if self.client:
                await self.client.ping()
                return True
            return False
        except Exception:
            return False
    
    # Queue operations
    async def lpush(self, key: str, value: str) -> int:
        """Left push to queue (high priority)"""
        if not self.client:
            raise DatabaseConnectionError("Redis not connected")
        return await self.client.lpush(key, value)
    
    async def rpush(self, key: str, value: str) -> int:
        """Right push to queue (normal priority)"""
        if not self.client:
            raise DatabaseConnectionError("Redis not connected")
        return await self.client.rpush(key, value)
    
    async def blpop(self, keys: List[str], timeout: int = 0) -> Optional[tuple]:
        """Blocking left pop from queue"""
        if not self.client:
            raise DatabaseConnectionError("Redis not connected")
        return await self.client.blpop(keys, timeout)
    
    async def llen(self, key: str) -> int:
        """Get queue length"""
        if not self.client:
            raise DatabaseConnectionError("Redis not connected")
        return await self.client.llen(key)
    
    # Cache operations
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cache value"""
        if not self.client:
            raise DatabaseConnectionError("Redis not connected")
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        return await self.client.set(key, value, ex=ttl)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        if not self.client:
            raise DatabaseConnectionError("Redis not connected")
        
        value = await self.client.get(key)
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    async def delete(self, key: str) -> int:
        """Delete cache key"""
        if not self.client:
            raise DatabaseConnectionError("Redis not connected")
        return await self.client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            raise DatabaseConnectionError("Redis not connected")
        return bool(await self.client.exists(key))
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set key expiration"""
        if not self.client:
            raise DatabaseConnectionError("Redis not connected")
        return await self.client.expire(key, ttl)
    
    # Hash operations
    async def hset(self, key: str, field: str, value: Any) -> int:
        """Set hash field"""
        if not self.client:
            raise DatabaseConnectionError("Redis not connected")
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        return await self.client.hset(key, field, value)
    
    async def hget(self, key: str, field: str) -> Optional[Any]:
        """Get hash field"""
        if not self.client:
            raise DatabaseConnectionError("Redis not connected")
        
        value = await self.client.hget(key, field)
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    async def hgetall(self, key: str) -> Dict[str, Any]:
        """Get all hash fields"""
        if not self.client:
            raise DatabaseConnectionError("Redis not connected")
        
        data = await self.client.hgetall(key)
        result = {}
        
        for field, value in data.items():
            try:
                result[field] = json.loads(value)
            except json.JSONDecodeError:
                result[field] = value
        
        return result
    
    async def hdel(self, key: str, field: str) -> int:
        """Delete hash field"""
        if not self.client:
            raise DatabaseConnectionError("Redis not connected")
        return await self.client.hdel(key, field)
    
    # Job queue specific operations
    async def enqueue_job(self, job_data: Dict[str, Any], priority: str = "normal") -> bool:
        """Enqueue a background job"""
        try:
            job_json = json.dumps(job_data)
            
            if priority == "high":
                await self.lpush(settings.REDIS_QUEUE_KEY, job_json)
            else:
                await self.rpush(settings.REDIS_QUEUE_KEY, job_json)
            
            logger.info(f"Job enqueued: {job_data.get('job_id', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            return False
    
    async def dequeue_job(self, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """Dequeue a background job"""
        try:
            result = await self.blpop([settings.REDIS_QUEUE_KEY], timeout)
            if result:
                _, job_json = result
                return json.loads(job_json)
            return None
            
        except Exception as e:
            logger.error(f"Failed to dequeue job: {e}")
            return None
    
    async def get_queue_size(self) -> int:
        """Get current queue size"""
        return await self.llen(settings.REDIS_QUEUE_KEY)


# Global Redis client instance
redis_client: Optional[RedisClient] = None


async def get_redis_client() -> RedisClient:
    """Get Redis client instance"""
    global redis_client
    if not redis_client:
        redis_client = await RedisClient.create()
    return redis_client
