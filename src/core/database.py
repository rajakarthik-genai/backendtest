"""
Database utilities for unified database access across the Medical Digital Twin API.

This module provides centralized database client management and utilities
for accessing MongoDB, Neo4j, Redis, and other database systems.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def get_database_clients() -> Dict[str, Any]:
    """
    Get all database clients in a unified dictionary.
    
    Returns:
        Dict containing all database clients:
        - mongodb: MongoDB database instance
        - neo4j: Neo4j connection
        - redis: Redis client
        - milvus: Milvus client
    """
    clients = {}
    
    # MongoDB
    try:
        from src.db.mongodb import get_database, is_mongo_available
        if is_mongo_available():
            clients["mongodb"] = get_database()
    except Exception as e:
        logger.warning(f"MongoDB not available: {e}")
        clients["mongodb"] = None
    
    # Neo4j  
    try:
        from src.db.neo4j import neo4j_connection
        if neo4j_connection.is_available():
            clients["neo4j"] = neo4j_connection
    except Exception as e:
        logger.warning(f"Neo4j not available: {e}")
        clients["neo4j"] = None
    
    # Redis
    try:
        from src.db.redis_client import get_redis_client
        # This is async, so we'll handle it differently in async contexts
        clients["redis"] = "available"  # Placeholder for async handling
    except Exception as e:
        logger.warning(f"Redis not available: {e}")
        clients["redis"] = None
    
    # Milvus
    try:
        # Milvus client would be available from app state
        clients["milvus"] = "available"  # Placeholder
    except Exception as e:
        logger.warning(f"Milvus not available: {e}")
        clients["milvus"] = None
        
    return clients

async def get_db_clients() -> Dict[str, Any]:
    """
    Async version to get database clients.
    
    Returns:
        Dict containing all available database clients
    """
    clients = {}
    
    # MongoDB
    try:
        from src.db.mongodb import get_database, is_mongo_available
        if is_mongo_available():
            clients["mongodb"] = get_database()
    except Exception as e:
        logger.warning(f"MongoDB not available: {e}")
        clients["mongodb"] = None
    
    # Neo4j  
    try:
        from src.db.neo4j import neo4j_connection
        if neo4j_connection.is_available():
            clients["neo4j"] = neo4j_connection
    except Exception as e:
        logger.warning(f"Neo4j not available: {e}")
        clients["neo4j"] = None
    
    # Redis
    try:
        from src.db.redis_client import get_redis_client
        redis_client = await get_redis_client()
        clients["redis"] = redis_client
    except Exception as e:
        logger.warning(f"Redis not available: {e}")
        clients["redis"] = None
    
    return clients

def get_mongo_client():
    """Return the underlying AsyncIOMotorClient instance for MongoDB."""
    try:
        from src.db.mongodb import mongodb  # local import to avoid circular deps
        return mongodb.client
    except Exception as exc:
        # In case MongoDB has not been initialised yet.
        logger.warning("MongoDB client is not initialised")
        return None

def get_neo4j_driver():
    """Return the Neo4j Bolt driver instance."""
    try:
        from src.db.neo4j import neo4j_connection  # local import
        return neo4j_connection.driver
    except Exception as exc:
        logger.warning("Neo4j driver is not initialised")
        return None
