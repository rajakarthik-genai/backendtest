# Updated for new modular structure
from src.core.config import settings
from .mongodb import connect_to_mongo, close_mongo_connection
from .redis_client import get_redis_client as redis_db
from .neo4j import neo4j_connection
# Milvus integration handled elsewhere

# Export initialized singletons/aliases for use elsewhere
# Mongo connection handled in src.main via lifespan
# NOTE: Neo4j and Milvus are initialized during app startup in main.py
# Do not initialize here to avoid import-time connection failures
# redis_db is already initialized in redis_db.py
