"""
Milvus helper (FAISS-GPU index) for semantic search & ingestion.

Functions
---------
init_milvus(host, port)          ▶ connect & lazy-load default collection.
add_document(doc_id, text)       ▶ embed + upsert one document.
query_text(query, top_k=3)       ▶ semantic search returning concatenated hits.
"""
from __future__ import annotations

import os
from typing import List
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
import openai

from config.settings import settings
from utils.logging import logger

# Singleton-like globals
_COLLECTION: Collection | None = None
_DIM: int = 1536  # embedding dimension of ada-002


def _get_collection_name() -> str:
    return os.getenv("MILVUS_COLLECTION", "medical_knowledge")


def _ensure_collection() -> Collection | None:
    """
    Create (if absent) and return the default collection with FAISS index.
    """
    global _COLLECTION
    name = _get_collection_name()
    if utility.has_collection(name):
        _COLLECTION = Collection(name)
    else:
        logger.info(f"Milvus: creating collection '{name}'")
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=_DIM),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=8192),
        ]
        schema = CollectionSchema(fields, description="Medical knowledge")
        _COLLECTION = Collection(name, schema)
        _COLLECTION.create_index(
            "embedding",
            {
                "index_type": "IVF_FLAT",
                "metric_type": "IP",
                "params": {"nlist": 1024},
            },
        )
    _COLLECTION.load()
    return _COLLECTION


def init_milvus(host: str = None, port: str | int = None) -> None:
    """
    Connect to Milvus and ensure the target collection is loaded.
    Safe to call multiple times.
    """
    host = host or settings.MILVUS_HOST
    port = port or settings.MILVUS_PORT
    try:
        connections.connect(alias="default", host=host, port=str(port))
        _ensure_collection()
        logger.info(f"Milvus connected at {host}:{port}")
    except Exception as exc:
        logger.error(f"Milvus init error: {exc}")


def _embed(text: str) -> List[float]:
    """
    Get an OpenAI Ada embedding. Cache-aware if you employ your own cache upstream.
    """
    resp = openai.Embedding.create(model="text-embedding-ada-002", input=text[:8192])
    return resp["data"][0]["embedding"]


def add_document(doc_id: str, text: str) -> None:
    """
    Insert or update a single document in the collection.
    """
    if not text:
        return
    if _COLLECTION is None:
        logger.warning("Milvus not initialised; skipping add_document.")
        return
    try:
        vec = _embed(text)
        _COLLECTION.upsert(
            [
                [doc_id],       # id field
                [vec],          # embedding field
                [text[:8191]],  # text field trimmed to max length
            ]
        )
        _COLLECTION.flush()
    except Exception as exc:
        logger.error(f"Milvus add_document error: {exc}")


def query_text(query: str, top_k: int = 3) -> str:
    """
    Run a semantic search and return concatenated top-k snippets.

    Returns
    -------
    str
        Short concatenation of texts from top hits (empty string if none).
    """
    if _COLLECTION is None:
        logger.warning("Milvus not initialised; returning empty search result.")
        return ""
    if not query.strip():
        return ""
    try:
        vec = _embed(query)
        res = _COLLECTION.search(
            data=[vec],
            anns_field="embedding",
            param={"metric_type": "IP", "params": {"nprobe": 10}},
            limit=top_k,
            output_fields=["text"],
        )
        hits = res[0]
        snippets = [hit.entity.get("text") for hit in hits]
        return " ".join(snippets)
    except Exception as exc:
        logger.error(f"Milvus query_text error: {exc}")
        return ""
