"""
Tools package – convenience wrappers used by agents, ingestion, and endpoints.

Exports:

    init_mongo(uri)
    init_graph(uri, user, pwd)
    init_milvus(host, port)

    # sub-modules (imported lazily by agents):
    document_db
    knowledge_graph
    vector_store
    web_search
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Optional
from src.utils.logging import logger

# Lazy-loader helpers (avoid heavy DB drivers until needed)
_modules: dict[str, ModuleType] = {}

def _load(name: str) -> ModuleType:
    if name not in _modules:
        _modules[name] = import_module(f"src.tools.{name}")
    return _modules[name]


# --------------------------------------------------------------------------- #
# Public re-exports (lazy)
# --------------------------------------------------------------------------- #
def __getattr__(item):
    if item in ("document_db", "knowledge_graph", "vector_store", "web_search"):
        return _load(item)
    raise AttributeError(item)


# --------------------------------------------------------------------------- #
# Init helpers called by app startup
# --------------------------------------------------------------------------- #
def init_mongo(uri: str):
    """Initialise Mongo connection for tools.document_db."""
    _load("document_db")._init(uri)


def init_graph(uri: str, user: str, pwd: str):
    """Initialise Neo4j driver for tools.knowledge_graph."""
    _load("knowledge_graph")._init(uri, user, pwd)


def init_milvus(host: str, port: int):
    """Initialise Milvus collection for tools.vector_store."""
    _load("vector_store")._init(host, port)
