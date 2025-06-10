"""
Thin wrapper over Milvus – compute embeddings (OpenAI or SentenceTransformers)
and provide insert/search helpers for agents.
"""

from __future__ import annotations

import openai, os
from typing import List
from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility,
)
from src.config.settings import settings
from src.utils.logging import logger

# ------------ global handles ------------------------------------------------
_collection: Collection | None = None
_DIM = 1536  # default OpenAI ada-002 dimensionality


def _init(host: str, port: int):
    connections.connect(alias="default", host=host, port=str(port))
    _ensure()


def _ensure():
    global _collection
    if _collection:
        return
    name = settings.milvus_collection
    if utility.has_collection(name):
        _collection = Collection(name)
    else:
        logger.info("tools.vector_store – creating collection '%s'", name)
        schema = CollectionSchema(
            [
                FieldSchema("id", DataType.VARCHAR, is_primary=True, max_length=64),
                FieldSchema("patient_id", DataType.VARCHAR, max_length=64),
                FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=_DIM),
            ]
        )
        _collection = Collection(name, schema)
        _collection.create_index(
            "embedding", {"index_type": "IVF_FLAT", "metric_type": "IP", "params": {"nlist": 2048}}
        )
    _collection.load()


# ------------------- helpers ------------------------------------------------
def _embed(text: str) -> List[float]:
    """Get OpenAI ada-002 embedding for text (fallback to dummy vector on error)."""
    try:
        resp = openai.Embedding.create(model="text-embedding-ada-002", input=text[:8192])
        return resp["data"][0]["embedding"]
    except Exception as exc:
        logger.error("Vector embed error: %s", exc)
        return [0.0] * _DIM


def insert_text(doc_id: str, patient_id: str, text: str):
    _ensure()
    vec = _embed(text)
    _collection.upsert([[doc_id], [patient_id], [vec]])
    _collection.flush()


def query_text(query: str, top_k: int = 5, patient_filter: str | None = None) -> str:
    _ensure()
    vec = _embed(query)
    expr = f'patient_id == "{patient_filter}"' if patient_filter else None
    res = _collection.search(
        [vec],
        anns_field="embedding",
        param={"metric_type": "IP", "params": {"nprobe": 16}},
        limit=top_k,
        expr=expr,
        output_fields=["id", "patient_id"],
    )
    if not res or len(res[0]) == 0:
        return "No semantic match."
    snippets = [f"{hit.entity.get('id')} (score {hit.distance:.2f})" for hit in res[0]]
    return "; ".join(snippets)
