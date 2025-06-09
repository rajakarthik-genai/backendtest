"""
Return body-part issues (and optionally its timeline).
"""
from fastapi import APIRouter, Query, Path
from neo4j import GraphDatabase
from src.config.settings import settings

router = APIRouter(prefix="/anatomy", tags=["anatomy"])

_driver = GraphDatabase.driver(
    settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
)


@router.get("/")
async def anatomy_overview(user_id: str = Query(...)):
    cypher = """
        MATCH (u:User {id:$uid})-[:HAS_INJURY]->(inj)-[:AFFECTS]->(b)
        RETURN b.name AS body_part,
               collect({name:inj.injury_type, date:inj.date, status:coalesce(inj.status,"Recovered")}) AS issues
    """
    with _driver.session() as s:
        recs = s.run(cypher, uid=user_id).data()
    return recs


@router.get("/{body_part}/timeline")
async def body_part_timeline(
    user_id: str = Query(...), body_part: str = Path(...)
):
    cypher = """
        MATCH (u:User {id:$uid})-[:HAS_INJURY]->(inj)-[:AFFECTS]->(b {name:$part})
        RETURN inj.date AS date, inj.injury_type AS name, inj.status AS status
        ORDER BY date
    """
    with _driver.session() as s:
        recs = s.run(cypher, uid=user_id, part=body_part).data()
    return recs
