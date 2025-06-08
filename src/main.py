from fastapi import FastAPI
from src.api.endpoints import chat, upload
from src.tools import (
    init_mongo, init_milvus, init_graph
)
from src.config.settings import settings
import os

app = FastAPI()

# Include routers
app.include_router(chat.router)
app.include_router(upload.router)

@app.on_event("startup")
def startup_event():
    # Initialize MongoDB
    mongo_uri = settings.MONGO_URI
    init_mongo(mongo_uri)
    # Initialize Milvus
    milvus_uri = settings.MILVUS_URI
    milvus_host = milvus_uri.replace("http://", "").split(":")[0]
    milvus_port = int(milvus_uri.split(":")[-1])
    init_milvus(host=milvus_host, port=milvus_port)
    # Initialize Neo4j
    neo4j_uri = settings.NEO4J_URI
    neo4j_user = settings.NEO4J_USER
    neo4j_password = settings.NEO4J_PASSWORD
    init_graph(neo4j_uri, neo4j_user, neo4j_password)
