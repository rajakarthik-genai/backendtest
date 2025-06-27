from src.config.settings import settings
from .mongo_db import MongoDB
from .redis_db import redis_db
from .neo4j_db import Neo4jDB, neo4j_db, init_graph
from .milvus_db import MilvusDB, milvus_db, init_milvus

# Export initialized singletons/aliases for use elsewhere
mongo_db = MongoDB()
# Initialize Neo4j and Milvus with settings
init_graph(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)
init_milvus(settings.milvus_host, settings.milvus_port)
# redis_db is already initialized in redis_db.py
