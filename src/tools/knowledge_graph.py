"""
Neo4j helper for Cypher execution and simple natural-language mapping.
"""
from __future__ import annotations
from neo4j import GraphDatabase, Driver
from src.utils.logging import logger

_driver: Driver | None = None


def init_graph(uri: str, user: str, password: str) -> None:
    """
    Initialise a global Neo4j driver. Safe to call repeatedly.
    """
    global _driver
    if _driver:
        return
    try:
        _driver = GraphDatabase.driver(uri, auth=(user, password))
        with _driver.session() as s:
            s.run("RETURN 1")
        logger.info("Neo4j connected.")
    except Exception as exc:
        logger.error(f"Neo4j init error: {exc}")


def run_cypher(query: str, **params) -> list[dict]:
    """
    Run a Cypher query and return result records as dictionaries.
    """
    if _driver is None:
        logger.warning("Neo4j not initialised.")
        return []
    try:
        with _driver.session() as session:
            records = session.run(query, **params)
            return [dict(rec) for rec in records]
    except Exception as exc:
        logger.error(f"Neo4j run_cypher error: {exc}")
        return []


def query_natural(nl: str) -> str:
    """
    VERY simple NL → Cypher mapping for demo purposes.
    Real deployment should use a proper NL-to-Cypher model or predefined templates.
    """
    nl_lc = nl.lower().strip("?")
    # Heuristic examples:
    if nl_lc.startswith("what causes"):
        # e.g., 'What causes migraine?'
        symptom = nl_lc.replace("what causes", "").strip()
        cypher = (
            "MATCH (s:Symptom)-[:INDICATES]->(c:Condition) "
            "WHERE toLower(s.name) CONTAINS $symptom "
            "RETURN DISTINCT c.name AS condition LIMIT 5"
        )
        recs = run_cypher(cypher, symptom=symptom)
        conds = [r["condition"] for r in recs]
        return ", ".join(conds) if conds else f"No known causes found for {symptom}."
    # Fallback: search node names
    cypher = (
        "MATCH (n) WHERE toLower(n.name) CONTAINS $name "
        "RETURN DISTINCT n.name AS name, labels(n)[0] AS label LIMIT 5"
    )
    recs = run_cypher(cypher, name=nl_lc)
    return "; ".join(f"{r['name']} ({r['label']})" for r in recs) or "No graph result."
