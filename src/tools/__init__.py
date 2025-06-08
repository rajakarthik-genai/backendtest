"""
tools package ── exposes *lazy-initialised* helpers for:
    • Web search                    → tools.web_search
    • Vector knowledge-base search  → tools.vector_store
    • Neo4j knowledge-graph query   → tools.knowledge_graph
    • Patient / report store (Mongo)→ tools.document_db
Initial-iser helpers are no-op if already connected, so they can be called
safely from `main.startup`, unit tests, or ad-hoc scripts.

Usage (agents):
    from tools import web_search, vector_store, knowledge_graph, document_db
"""
from src.tools.web_search      import search
from src.tools.vector_store    import init_milvus, query_text, add_document
from src.tools.knowledge_graph import init_graph, run_cypher, query_natural
from src.tools.document_db     import init_mongo, get_patient_profile, get_patient_record
__all__ = [
    # web search
    "search",
    # vector store
    "init_milvus", "query_text", "add_document",
    # graph
    "init_graph", "run_cypher", "query_natural",
    # document db
    "init_mongo", "get_patient_profile", "get_patient_record",
]
