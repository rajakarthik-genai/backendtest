from src.config.settings import settings
from .mongo_db import MongoDB
from .redis_db import redis_db
from .neo4j_db import Neo4jDB, neo4j_db, init_graph
from .milvus_db import MilvusDB, milvus_db, init_milvus

# Export initialized singletons/aliases for use elsewhere
mongo_db = MongoDB()
# NOTE: Neo4j and Milvus are initialized during app startup in main.py
# Do not initialize here to avoid import-time connection failures
# redis_db is already initialized in redis_db.py
