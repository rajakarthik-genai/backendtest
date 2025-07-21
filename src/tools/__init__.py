"""
Tools package – convenience wrappers used by agents, ingestion, and endpoints.

This module provides lazy-loaded access to various medical tools and databases:
- Document processing and storage
- Knowledge graph operations  
- Vector similarity search
- Web search capabilities

The tools are imported on-demand to avoid loading heavy dependencies at startup.
"""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Optional
from src.utils.logging import logger

# Lazy-loader helpers (avoid heavy DB drivers until needed)
_modules: dict[str, ModuleType] = {}

def _load(name: str) -> ModuleType:
    """Lazy load a tool module."""
    if name not in _modules:
        try:
            _modules[name] = import_module(f"src.tools.{name}")
        except ImportError as e:
            logger.error(f"Failed to load tool module {name}: {e}")
            raise
    return _modules[name]


# --------------------------------------------------------------------------- #
# Public re-exports (lazy)
# --------------------------------------------------------------------------- #
def __getattr__(item):
    """Lazy attribute access for tool modules."""
    if item in ("document_db", "knowledge_graph", "vector_store", "web_search", "pdf_extractor"):
        return _load(item)
    raise AttributeError(f"Module 'tools' has no attribute '{item}'")


# --------------------------------------------------------------------------- #
# Compatibility exports - these are now handled by individual DB modules
# --------------------------------------------------------------------------- #

# Note: The init functions are now handled by individual database modules
# This maintains backwards compatibility while using the new architecture

def init_mongo(uri: str, db_name: str = "digital_twin"):
    """
    Initialize MongoDB connection (compatibility function).
    
    The actual initialization is now handled by src.db.mongo_db.init_mongo()
    """
    logger.warning("tools.init_mongo is deprecated. Use src.db.mongo_db.init_mongo() instead.")
    
    try:
        from src.db.mongo_db import init_mongo as mongo_init
        # This is now async, so we can't call it directly here
        logger.info("MongoDB initialization delegated to main startup")
    except ImportError as e:
        logger.error(f"Failed to import MongoDB init: {e}")


def init_graph(uri: str, user: str, pwd: str):
    """
    Initialize Neo4j connection (compatibility function).
    
    The actual initialization is now handled by src.db.neo4j_db.init_graph()
    """
    logger.warning("tools.init_graph is deprecated. Use src.db.neo4j_db.init_graph() instead.")
    
    try:
        from src.db.neo4j_db import init_graph as neo4j_init
        neo4j_init(uri, user, pwd)
        logger.info("Neo4j initialized via compatibility layer")
    except ImportError as e:
        logger.error(f"Failed to import Neo4j init: {e}")


def init_milvus(host: str, port: int = 19530):
    """
    Initialize Milvus connection (compatibility function).
    
    The actual initialization is now handled by src.db.milvus_db.init_milvus()
    """
    logger.warning("tools.init_milvus is deprecated. Use src.db.milvus_db.init_milvus() instead.")
    
    try:
        from src.db.milvus_db import init_milvus as milvus_init
        milvus_init(host, port)
        logger.info("Milvus initialized via compatibility layer")
    except ImportError as e:
        logger.error(f"Failed to import Milvus init: {e}")


# --------------------------------------------------------------------------- #
# Tool factory functions
# --------------------------------------------------------------------------- #

def get_document_db():
    """Get document database tool."""
    return _load("document_db")


def get_knowledge_graph():
    """Get knowledge graph tool.""" 
    return _load("knowledge_graph")


def get_vector_store():
    """Get vector store tool (using new MilvusDB system)."""
    from src.db.milvus_db import get_milvus
    return get_milvus()


def get_web_search():
    """Get web search tool."""
    return _load("web_search")


def get_pdf_extractor():
    """Get PDF extraction tool."""
    return _load("pdf_extractor")
