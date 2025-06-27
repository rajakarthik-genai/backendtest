"""
Neo4j knowledge graph database for medical relationships and anatomy.

Handles:
- Patient-Event-BodyPart relationships
- Medical condition associations
- Anatomical structure modeling
- User data isolation via hashed user_ids
"""

import hashlib
import hmac
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from neo4j import GraphDatabase, Transaction
from neo4j.exceptions import Neo4jError

from src.config.settings import settings
from src.utils.logging import logger


class Neo4jDB:
    """Neo4j knowledge graph manager for medical relationships."""
    
    def __init__(self):
        self.driver = None
        self._initialized = False
    
    def initialize(self, uri: str, username: str, password: str):
        """Initialize Neo4j connection."""
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            
            # Create constraints and indexes
            self._create_constraints()
            
            self._initialized = True
            logger.info(f"Neo4j connected to {uri}")
            
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            raise
    
    def _create_constraints(self):
        """Create constraints and indexes for performance."""
        try:
            with self.driver.session() as session:
                # Create unique constraints
                session.run("CREATE CONSTRAINT patient_id_unique IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE")
                session.run("CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE")
                session.run("CREATE CONSTRAINT body_part_name_unique IF NOT EXISTS FOR (b:BodyPart) REQUIRE b.name IS UNIQUE")
                
                # Create indexes for performance
                session.run("CREATE INDEX patient_user_id_index IF NOT EXISTS FOR (p:Patient) ON (p.user_id)")
                session.run("CREATE INDEX event_timestamp_index IF NOT EXISTS FOR (e:Event) ON (e.timestamp)")
                session.run("CREATE INDEX event_type_index IF NOT EXISTS FOR (e:Event) ON (e.event_type)")
                
            logger.info("Neo4j constraints and indexes created")
            
        except Exception as e:
            logger.error(f"Failed to create Neo4j constraints: {e}")
            raise
    
    def _hash_user_id(self, user_id: str, secret_key: str = None) -> str:
        """Create consistent hash of user_id for data isolation."""
        if not secret_key:
            secret_key = settings.neo4j_password
        
        return hmac.new(
            secret_key.encode(),
            user_id.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _identify_body_parts(self, text: str) -> List[str]:
        """Extract body parts from text using keyword matching."""
        if not text:
            return []
        
        text_lower = text.lower()
        body_parts = set()
        
        # Common body part keywords
        body_part_map = {
            "heart": "Heart",
            "cardiac": "Heart",
            "lung": "Lung",
            "pulmonary": "Lung",
            "liver": "Liver",
            "hepatic": "Liver",
            "kidney": "Kidney",
            "renal": "Kidney",
            "brain": "Brain",
            "cerebral": "Brain",
            "shoulder": "Shoulder",
            "arm": "Arm",
            "leg": "Leg",
            "knee": "Knee",
            "hip": "Hip",
            "spine": "Spine",
            "spinal": "Spine",
            "stomach": "Stomach",
            "gastric": "Stomach",
            "eye": "Eye",
            "ocular": "Eye",
            "ear": "Ear",
            "skin": "Skin",
            "dermal": "Skin"
        }
        
        for keyword, body_part in body_part_map.items():
            if keyword in text_lower:
                # Check for laterality
                if "right" in text_lower and keyword in text_lower:
                    body_parts.add(f"Right {body_part}")
                elif "left" in text_lower and keyword in text_lower:
                    body_parts.add(f"Left {body_part}")
                else:
                    body_parts.add(body_part)
        
        return list(body_parts)
    
    def create_patient_node(self, user_id: str, patient_data: Dict[str, Any]) -> bool:
        """Create or update a patient node."""
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            with self.driver.session() as session:
                query = """
                MERGE (p:Patient {patient_id: $patient_id})
                SET p.user_id = $user_id,
                    p.age = $age,
                    p.gender = $gender,
                    p.created_at = $created_at,
                    p.updated_at = $updated_at
                RETURN p
                """
                
                result = session.run(query, {
                    "patient_id": hashed_user_id,
                    "user_id": hashed_user_id,
                    "age": patient_data.get("age"),
                    "gender": patient_data.get("gender"),
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Patient node created/updated for user {user_id[:8]}...")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create patient node: {e}")
            return False
    
    def create_medical_event(
        self,
        user_id: str,
        event_data: Dict[str, Any]
    ) -> str:
        """Create a medical event node and connect to patient and body parts."""
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            event_id = f"event_{hashed_user_id}_{datetime.utcnow().timestamp()}"
            
            # Extract body parts from event description
            description = event_data.get("description", "")
            title = event_data.get("title", "")
            body_parts = self._identify_body_parts(f"{title} {description}")
            
            with self.driver.session() as session:
                # Create event node
                event_query = """
                MATCH (p:Patient {patient_id: $patient_id})
                CREATE (e:Event {
                    event_id: $event_id,
                    title: $title,
                    description: $description,
                    event_type: $event_type,
                    timestamp: $timestamp,
                    severity: $severity,
                    created_at: $created_at
                })
                CREATE (p)-[:HAS_EVENT]->(e)
                RETURN e
                """
                
                session.run(event_query, {
                    "patient_id": hashed_user_id,
                    "event_id": event_id,
                    "title": event_data.get("title", ""),
                    "description": description,
                    "event_type": event_data.get("event_type", "general"),
                    "timestamp": event_data.get("timestamp", datetime.utcnow()).isoformat(),
                    "severity": event_data.get("severity", "medium"),
                    "created_at": datetime.utcnow().isoformat()
                })
                
                # Create body part connections
                for body_part in body_parts:
                    body_part_query = """
                    MERGE (b:BodyPart {name: $body_part_name})
                    WITH b
                    MATCH (e:Event {event_id: $event_id})
                    CREATE (e)-[:AFFECTS]->(b)
                    """
                    
                    session.run(body_part_query, {
                        "body_part_name": body_part,
                        "event_id": event_id
                    })
                
                logger.info(f"Medical event created: {event_id}")
                return event_id
                
        except Exception as e:
            logger.error(f"Failed to create medical event: {e}")
            raise
    
    def get_patient_timeline(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chronological timeline of patient events."""
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            with self.driver.session() as session:
                query = """
                MATCH (p:Patient {patient_id: $patient_id})-[:HAS_EVENT]->(e:Event)
                OPTIONAL MATCH (e)-[:AFFECTS]->(b:BodyPart)
                WITH e, collect(b.name) as affected_parts
                RETURN e.event_id as event_id,
                       e.title as title,
                       e.description as description,
                       e.event_type as event_type,
                       e.timestamp as timestamp,
                       e.severity as severity,
                       affected_parts
                ORDER BY e.timestamp DESC
                LIMIT $limit
                """
                
                result = session.run(query, {
                    "patient_id": hashed_user_id,
                    "limit": limit
                })
                
                events = []
                for record in result:
                    events.append({
                        "event_id": record["event_id"],
                        "title": record["title"],
                        "description": record["description"],
                        "event_type": record["event_type"],
                        "timestamp": record["timestamp"],
                        "severity": record["severity"],
                        "affected_body_parts": record["affected_parts"]
                    })
                
                return events
                
        except Exception as e:
            logger.error(f"Failed to get patient timeline: {e}")
            return []
    
    def get_body_part_history(self, user_id: str, body_part: str) -> List[Dict[str, Any]]:
        """Get all events affecting a specific body part for a user."""
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            with self.driver.session() as session:
                query = """
                MATCH (p:Patient {patient_id: $patient_id})-[:HAS_EVENT]->(e:Event)-[:AFFECTS]->(b:BodyPart {name: $body_part})
                RETURN e.event_id as event_id,
                       e.title as title,
                       e.description as description,
                       e.event_type as event_type,
                       e.timestamp as timestamp,
                       e.severity as severity
                ORDER BY e.timestamp DESC
                """
                
                result = session.run(query, {
                    "patient_id": hashed_user_id,
                    "body_part": body_part
                })
                
                events = []
                for record in result:
                    events.append({
                        "event_id": record["event_id"],
                        "title": record["title"],
                        "description": record["description"],
                        "event_type": record["event_type"],
                        "timestamp": record["timestamp"],
                        "severity": record["severity"]
                    })
                
                return events
                
        except Exception as e:
            logger.error(f"Failed to get body part history: {e}")
            return []
    
    def get_related_conditions(self, user_id: str, condition: str) -> List[Dict[str, Any]]:
        """Find related medical conditions through body part connections."""
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            with self.driver.session() as session:
                query = """
                MATCH (p:Patient {patient_id: $patient_id})-[:HAS_EVENT]->(e1:Event)-[:AFFECTS]->(b:BodyPart)<-[:AFFECTS]-(e2:Event)<-[:HAS_EVENT]-(p)
                WHERE e1.title CONTAINS $condition OR e1.description CONTAINS $condition
                AND e1 <> e2
                RETURN DISTINCT e2.title as related_condition,
                       e2.description as description,
                       e2.event_type as event_type,
                       e2.timestamp as timestamp,
                       b.name as shared_body_part
                ORDER BY e2.timestamp DESC
                """
                
                result = session.run(query, {
                    "patient_id": hashed_user_id,
                    "condition": condition
                })
                
                related = []
                for record in result:
                    related.append({
                        "condition": record["related_condition"],
                        "description": record["description"],
                        "event_type": record["event_type"],
                        "timestamp": record["timestamp"],
                        "shared_body_part": record["shared_body_part"]
                    })
                
                return related
                
        except Exception as e:
            logger.error(f"Failed to get related conditions: {e}")
            return []
    
    def delete_medical_event(
        self,
        user_id: str,
        event_id: str
    ) -> bool:
        """Delete a medical event node and its relationships."""
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            with self.driver.session() as session:
                # Delete event and all its relationships
                delete_query = """
                MATCH (p:Patient {patient_id: $patient_id})-[:HAS_EVENT]->(e:Event)
                WHERE e.event_id = $event_id OR toString(id(e)) = $event_id
                DETACH DELETE e
                RETURN count(e) as deleted_count
                """
                
                result = session.run(delete_query, {
                    "patient_id": hashed_user_id,
                    "event_id": event_id
                })
                
                record = result.single()
                deleted_count = record["deleted_count"] if record else 0
                
                logger.info(f"Deleted medical event {event_id}: {deleted_count > 0}")
                return deleted_count > 0
                
        except Exception as e:
            logger.error(f"Failed to delete medical event: {e}")
            return False

    def update_medical_event(
        self,
        user_id: str,
        event_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """Update a medical event node."""
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            with self.driver.session() as session:
                # Build the SET clause dynamically
                set_clauses = []
                params = {
                    "patient_id": hashed_user_id,
                    "event_id": event_id,
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                for key, value in update_data.items():
                    if key in ["title", "description", "event_type", "severity"]:
                        set_clauses.append(f"e.{key} = ${key}")
                        params[key] = value
                    elif key == "timestamp":
                        set_clauses.append("e.timestamp = $timestamp")
                        params["timestamp"] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                
                if not set_clauses:
                    return True  # Nothing to update
                
                set_clauses.append("e.updated_at = $updated_at")
                set_clause = ", ".join(set_clauses)
                
                update_query = f"""
                MATCH (p:Patient {{patient_id: $patient_id}})-[:HAS_EVENT]->(e:Event)
                WHERE e.event_id = $event_id OR toString(id(e)) = $event_id
                SET {set_clause}
                RETURN count(e) as updated_count
                """
                
                result = session.run(update_query, params)
                record = result.single()
                updated_count = record["updated_count"] if record else 0
                
                logger.info(f"Updated medical event {event_id}: {updated_count > 0}")
                return updated_count > 0
                
        except Exception as e:
            logger.error(f"Failed to update medical event: {e}")
            return False

    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")


# Global Neo4j instance
neo4j_db = Neo4jDB()


def init_graph(uri: str, username: str, password: str):
    """Initialize global Neo4j instance."""
    neo4j_db.initialize(uri, username, password)


def get_graph() -> Neo4jDB:
    """Get Neo4j instance."""
    if not neo4j_db._initialized:
        raise RuntimeError("Neo4j not initialized. Call init_graph() first.")
    return neo4j_db
