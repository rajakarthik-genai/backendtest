"""
Utility wrapper for Neo4j – run arbitrary Cypher queries or a naive NL->Cypher
mapping for quick knowledge look-ups.
"""

from __future__ import annotations

from neo4j import GraphDatabase, Driver
from src.utils.logging import logger

_driver: Driver | None = None


def _init(uri: str, user: str, pwd: str):
    global _driver
    if _driver:
        return
    try:
        _driver = GraphDatabase.driver(uri, auth=(user, pwd))
        with _driver.session() as sess:
            sess.run("RETURN 1")
        logger.info("tools.knowledge_graph – Neo4j connected.")
    except Exception as exc:
        logger.error("tools.knowledge_graph – connection error: %s", exc)


def run(query: str, **params):
    """Run Cypher and return list of dicts."""
    if _driver is None:
        return []
    with _driver.session() as sess:
        recs = sess.run(query, **params)
        return [dict(r) for r in recs]


# --- naïve NL -> Cypher mapping (demo) ------------------------------------ #
def query_natural(nl: str) -> str:
    """
    VERY rudimentary mapping for demo purposes.
    Accepts questions like:
        "what causes chest pain"
        "injuries to right shoulder"
    """
    q = nl.lower()
    if "injuries" in q and "shoulder" in q:
        side = "Right" if "right" in q else "Left" if "left" in q else ""
        part = f"{side} Shoulder".strip()
        cypher = (
            "MATCH (p:Patient)-[:HAS_CONDITION|HAS_EVENT]->(e)-[:AFFECTS]->(b:BodyPart {name:$part}) "
            "RETURN e.metric AS metric, e.timestamp AS ts ORDER BY ts"
        )
        res = run(cypher, part=part)
        if not res:
            return f"No injury events found for {part}."
        return "; ".join(f"{r['metric']} ({r['ts']})" for r in res)
    # fallback generic node search
    cypher = "MATCH (n) WHERE toLower(n.name) CONTAINS $name RETURN DISTINCT n.name AS name LIMIT 5"
    res = run(cypher, name=q)
    return ", ".join(r["name"] for r in res) or "No graph result."
