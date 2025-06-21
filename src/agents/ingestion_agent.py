"""
Asynchronous ingestion task for uploaded PDFs/images.
Extracts text, calls LLM for structuring, stores data.
"""

import json, asyncio, openai, os
from bson import ObjectId
from langchain_neo4j import Neo4jGraph

from src.utils.logging import logger
from src.config.settings import settings
from src.tools import pdf_extractor, document_db, vector_store
from src.db.mongo_db import MongoDBClient as MongoDB

openai.api_key = settings.openai_api_key
mongo = MongoDB()

# Initialise the graph with required parameters
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    refresh_schema=False,     # skips apoc.meta.data()
)

async def ingest_pdf(user_id: str, file_path: str, ingest_log_id: str):
    logger.info("Ingestion started for %s", file_path)
    # 1. Extract text
    text = pdf_extractor.extract_pdf_text(file_path)
    # 2. Ask GPT to structure
    prompt = (
        "Extract structured JSON with keys: lab_results, medications, conditions, injuries. "
        "Keep raw values, include units."
    )
    try:
        resp = openai.ChatCompletion.create(
            model=settings.openai_model_chat,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text[:15000]},
            ],
            temperature=0,
        )
        data = json.loads(resp.choices[0].message.content)
    except Exception as exc:
        logger.error("LLM extraction failed: %s", exc)
        mongo.db.ingest_logs.update_one(
            {"_id": ObjectId(ingest_log_id)}, {"$set": {"status": "failed", "error": str(exc)}}
        )
        return
    # 3. Save raw report
    report_id = mongo.create_report(user_id, content=text, file_name=os.path.basename(file_path))
    # 4. Process extracted data (simplified)
    for cond in data.get("conditions", []):
        mongo.db.conditions.insert_one({**cond, "user_id": user_id, "report_id": report_id})
    # 5. Index report in Milvus
    vector_store.add_document(report_id, text)
    # 6. Mark ingestion completed
    mongo.db.ingest_logs.update_one(
        {"_id": ObjectId(ingest_log_id)}, {"$set": {"status": "completed"}}
    )
    logger.info("Ingestion complete for %s", file_path)
