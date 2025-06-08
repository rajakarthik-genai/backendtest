from fastapi import FastAPI
from src.api.endpoints import chat, upload
from src.tools import (
    init_mongo, init_milvus, init_graph
)
import os

app = FastAPI()

# Include routers
app.include_router(chat.router)
app.include_router(upload.router)

@app.on_event("startup")
def startup_event():
    # Initialize MongoDB
    mongo_uri = os.getenv("MONGO_URI", "mongodb://admin:supersecret@mongo:27017")
    init_mongo(mongo_uri)
    # Initialize Milvus
    milvus_uri = os.getenv("MILVUS_URI", "milvus")
    milvus_host = milvus_uri.replace("http://", "").split(":")[0]
    milvus_port = milvus_uri.split(":")[-1]
    init_milvus(host=milvus_host, port=milvus_port)
    # Initialize Neo4j
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "anothersecret")
    init_graph(neo4j_uri, neo4j_user, neo4j_password)
