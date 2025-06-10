"""
/anatomy – body-part–centric queries via Neo4j.
"""

from fastapi import APIRouter, Query, Path
from src.tools import knowledge_graph as kg

router = APIRouter(prefix="/anatomy", tags=["anatomy"])


@router.get("/")
async def anatomy_overview(user_id: str = Query(...)):
    """
    Summarise issues grouped by BodyPart for the specified user.
    """
    cypher = (
        "MATCH (p:Patient {id:$uid})-[:HAS_CONDITION|HAS_EVENT]->(rel)-[:AFFECTS]->(b:BodyPart) "
        "RETURN b.name AS body_part, "
        "collect({metric: rel.metric, ts: rel.timestamp, val: rel.value}) AS issues"
    )
    rows = kg.run(cypher, uid=user_id)
    return rows


@router.get("/{body_part}/timeline")
async def part_timeline(
    user_id: str = Query(...),
    body_part: str = Path(..., description="e.g. 'Right Shoulder' or 'Heart'"),
):
    cypher = (
        "MATCH (p:Patient {id:$uid})-[:HAS_CONDITION|HAS_EVENT]->(rel)-[:AFFECTS]->"
        "(b:BodyPart {name:$part}) "
        "RETURN rel.metric AS metric, rel.timestamp AS ts, rel.value AS value "
        "ORDER BY ts"
    )
    rows = kg.run(cypher, uid=user_id, part=body_part)
    return rows
