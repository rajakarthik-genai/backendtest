from src.config.settings import settings
from .mongo_db import MongoDBClient
from .redis_db import redis_client
from .neo4j_db import Neo4jGraphBuilder
from .milvus_db import MilvusIndexer

# Export initialized singletons/aliases for use elsewhere
mongo_db = MongoDBClient()
neo4j_driver = Neo4jGraphBuilder(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
milvus_collection = MilvusIndexer(settings.milvus_host, settings.milvus_port, settings.milvus_collection)
# redis_client is already initialized in redis_db.py
