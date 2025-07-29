"""
Database utilities for unified database access across the Medical Digital Twin API.

This module provides centralized database client management and utilities
for accessing MongoDB, Neo4j, Redis, and other database systems.
"""

from typing import Dict, Any, Optional
from src.db.mongodb import get_database
from src.db.neo4j import Neo4jConnection
from src.db.redis_db import get_redis
from src.db.milvus_client import MilvusClient


def get_database_clients() -> Dict[str, Any]:
    """
    Get all database clients in a unified dictionary.
    
    Returns:
        Dict containing all database clients:
        - mongo: MongoDB client
        - neo4j: Neo4j driver
        - redis: Redis client
        - milvus: Milvus client
    """
    return {
        "mongo": get_mongo_client(),
        "neo4j": get_neo4j_driver(),
        "redis": get_redis_client(),
        "milvus": get_milvus_client(),
    }


def get_mongo_client():
    """Return the underlying AsyncIOMotorClient instance for MongoDB.
    This avoids recursive calls by accessing the global singleton
    managed in ``src.db.mongodb``.
    """
    try:
        from src.db.mongodb import mongodb  # local import to avoid circular deps
        return mongodb.client
    except Exception as exc:
        # In case MongoDB has not been initialised yet.
        raise RuntimeError("MongoDB client is not initialised") from exc


def get_neo4j_driver():
    """Return the Neo4j Bolt driver instance."""
    from src.db.neo4j import neo4j_connection  # local import
    return neo4j_connection.driver


def get_redis_client():
    """Return the low-level Redis client (sync or mock)."""
    try:
        from src.db.redis_client import get_redis_client as get_redis_instance
        return get_redis_instance()
    except Exception as exc:
        raise RuntimeError("Redis client is not initialised") from exc


_milvus_client: Optional[MilvusClient] = None

def get_milvus_client():
    """Return a singleton MilvusClient instance."""
    global _milvus_client
    if _milvus_client is None:
        _milvus_client = MilvusClient()
    return _milvus_client
