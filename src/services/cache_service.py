"""
Caching Service for Medical Digital Twin API
Provides Redis-based caching for frequently accessed data

Features:
- Patient data caching
- Document metadata caching
- Medical entity caching
- Configurable TTL values
- Cache invalidation strategies
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import timedelta
import asyncio

from src.db.redis_client import get_redis_client

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service"""
    
    def __init__(self):
        self.redis = None
        self.default_ttl = 3600  # 1 hour
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis = await get_redis_client()
            if self.redis:
                logger.info("Cache service initialized successfully")
                return True
        except Exception as e:
            logger.error(f"Cache service initialization failed: {e}")
        return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis:
            return None
            
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        if not self.redis:
            return False
            
        try:
            ttl = ttl or self.default_ttl
            await self.redis.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
        return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis:
            return False
            
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
        return False
    
    async def get_patient_documents(self, patient_id: str) -> Optional[List[Dict]]:
        """Get cached patient documents"""
        key = f"patient_docs:{patient_id}"
        return await self.get(key)
    
    async def cache_patient_documents(self, patient_id: str, documents: List[Dict], ttl: int = 600) -> bool:
        """Cache patient documents (10 min TTL)"""
        key = f"patient_docs:{patient_id}"
        return await self.set(key, documents, ttl)
    
    async def invalidate_patient_cache(self, patient_id: str) -> bool:
        """Invalidate all patient-related cache"""
        keys_to_delete = [
            f"patient_docs:{patient_id}",
            f"patient_entities:{patient_id}",
            f"patient_timeline:{patient_id}"
        ]
        
        success = True
        for key in keys_to_delete:
            if not await self.delete(key):
                success = False
        
        return success
    
    async def get_medical_entities(self, patient_id: str) -> Optional[Dict]:
        """Get cached medical entities"""
        key = f"patient_entities:{patient_id}"
        return await self.get(key)
    
    async def cache_medical_entities(self, patient_id: str, entities: Dict, ttl: int = 1800) -> bool:
        """Cache medical entities (30 min TTL)"""
        key = f"patient_entities:{patient_id}"
        return await self.set(key, entities, ttl)

# Global cache service instance
cache_service = CacheService()

async def init_cache_service() -> bool:
    """Initialize cache service"""
    return await cache_service.initialize()

def get_cache_service() -> CacheService:
    """Get cache service instance"""
    return cache_service
