"""
/anatomy – body-part–centric queries via Neo4j.
"""

from fastapi import APIRouter, Path, Depends
from src.tools import knowledge_graph as kg
from src.auth.dependencies import CurrentUser
from src.auth.models import User

router = APIRouter(prefix="/anatomy", tags=["anatomy"])


@router.get("/")
async def anatomy_overview(current_user: CurrentUser):
    """
    Summarise issues grouped by BodyPart for the specified user.
    """
    user_id = current_user.user_id
    
    cypher = (
        "MATCH (p:Patient {id:$uid})-[:HAS_CONDITION|HAS_EVENT]->(rel)-[:AFFECTS]->(b:BodyPart) "
        "RETURN b.name AS body_part, "
        "collect({metric: rel.metric, ts: rel.timestamp, val: rel.value}) AS issues"
    )
    rows = kg.run(cypher, uid=user_id)
    return rows


@router.get("/{body_part}/timeline")
async def part_timeline(
    current_user: CurrentUser,
    body_part: str = Path(..., description="e.g. 'Right Shoulder' or 'Heart'")
):
    """
    Get timeline of events for a specific body part.
    """
    user_id = current_user.user_id
    
    cypher = (
        "MATCH (p:Patient {id:$uid})-[:HAS_CONDITION|HAS_EVENT]->(rel)-[:AFFECTS]->"
        "(b:BodyPart {name:$part}) "
        "RETURN rel.metric AS metric, rel.timestamp AS ts, rel.value AS value "
        "ORDER BY ts"
    )
    rows = kg.run(cypher, uid=user_id, part=body_part)
    return rows
