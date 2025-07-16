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
                # Drop old body part constraint if it exists
                try:
                    session.run("DROP CONSTRAINT body_part_name_unique IF EXISTS")
                except:
                    pass
                
                # Create unique constraints
                session.run("CREATE CONSTRAINT patient_id_unique IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE")
                session.run("CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE")
                
                # Create patient-specific body part constraint
                session.run("CREATE CONSTRAINT unique_bodypart_per_user IF NOT EXISTS FOR (b:BodyPart) REQUIRE (b.patient_id, b.name) IS UNIQUE")
                
                # Create indexes for performance
                session.run("CREATE INDEX patient_user_id_index IF NOT EXISTS FOR (p:Patient) ON (p.user_id)")
                session.run("CREATE INDEX event_timestamp_index IF NOT EXISTS FOR (e:Event) ON (e.timestamp)")
                session.run("CREATE INDEX event_type_index IF NOT EXISTS FOR (e:Event) ON (e.event_type)")
                session.run("CREATE INDEX bodypart_patient_index IF NOT EXISTS FOR (b:BodyPart) ON (b.patient_id)")
                
            logger.info("Neo4j constraints and indexes created with patient-specific body parts")
            
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
        from src.config.body_parts import identify_body_parts_from_text
        return identify_body_parts_from_text(text)
    
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
        event_data: Dict[str, Any],
        body_parts: List[str] = None
    ) -> str:
        """Create a medical event node and connect to patient and body parts."""
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        try:
            # Ensure user is initialized first
            self.ensure_user_initialized(user_id)
            
            hashed_user_id = self._hash_user_id(user_id)
            event_id = f"event_{hashed_user_id}_{int(datetime.utcnow().timestamp() * 1000)}"
            
            # Use provided body parts or extract from text
            if body_parts:
                affected_body_parts = body_parts
            else:
                # Fallback to text extraction
                description = event_data.get("description", "")
                title = event_data.get("title", "")
                affected_body_parts = self._identify_body_parts(f"{title} {description}")
            
            with self.driver.session() as session:
                # Create event node with enhanced properties
                event_query = """
                MATCH (p:Patient {patient_id: $patient_id})
                CREATE (e:Event {
                    event_id: $event_id,
                    title: $title,
                    description: $description,
                    event_type: $event_type,
                    timestamp: $timestamp,
                    severity: $severity,
                    confidence: $confidence,
                    source: $source,
                    extraction_method: $extraction_method,
                    created_at: $created_at
                })
                CREATE (p)-[:HAS_EVENT]->(e)
                RETURN e
                """
                
                session.run(event_query, {
                    "patient_id": hashed_user_id,
                    "event_id": event_id,
                    "title": event_data.get("title", ""),
                    "description": event_data.get("description", ""),
                    "event_type": event_data.get("event_type", "general"),
                    "timestamp": event_data.get("timestamp", datetime.utcnow()).isoformat(),
                    "severity": event_data.get("severity", "mild"),
                    "confidence": event_data.get("confidence", 0.8),
                    "source": event_data.get("source", "document_processing"),
                    "extraction_method": event_data.get("extraction_method", "unknown"),
                    "created_at": datetime.utcnow().isoformat()
                })
                
                # Create body part connections using patient-specific body parts
                for body_part in affected_body_parts:
                    body_part_query = """
                    MATCH (p:Patient {patient_id: $patient_id})
                    MERGE (b:BodyPart {name: $body_part_name, patient_id: $patient_id})
                    MERGE (p)-[:HAS_BODY_PART]->(b)
                    WITH e, b
                    MATCH (e:Event {event_id: $event_id})
                    CREATE (e)-[:AFFECTS]->(b)
                    """
                    
                    session.run(body_part_query, {
                        "body_part_name": body_part,
                        "patient_id": hashed_user_id,
                        "event_id": event_id
                    })
                
                # Update event count for affected body parts
                if affected_body_parts:
                    count_query = """
                    MATCH (p:Patient {patient_id: $patient_id})-[r:HAS_BODY_PART]->(b:BodyPart {patient_id: $patient_id})
                    WHERE b.name IN $body_parts
                    SET r.event_count = coalesce(r.event_count, 0) + 1,
                        r.last_updated = $updated_at
                    """
                    
                    session.run(count_query, {
                        "patient_id": hashed_user_id,
                        "body_parts": affected_body_parts,
                        "updated_at": datetime.utcnow().isoformat()
                    })
                
                logger.info(f"Medical event created: {event_id} affecting {len(affected_body_parts)} body parts")
                
                # Auto-update severity for affected body parts
                for body_part in affected_body_parts:
                    new_severity = self.calculate_severity_from_events(user_id, body_part)
                    self.update_body_part_severity(user_id, body_part, new_severity)
                
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
    
    def get_body_part_history(self, user_id: str, body_part: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get history of events for a specific body part."""
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            with self.driver.session() as session:
                query = """
                MATCH (p:Patient {patient_id: $patient_id})-[:HAS_EVENT]->(e:Event)-[:AFFECTS]->(b:BodyPart {name: $body_part, patient_id: $patient_id})
                RETURN e.event_id as id,
                       e.title as title,
                       e.description as description,
                       e.timestamp as timestamp,
                       e.severity as severity,
                       e.event_type as type,
                       e.confidence as confidence,
                       e.source as source
                ORDER BY e.timestamp DESC
                LIMIT $limit
                """
                
                result = session.run(query, {
                    "patient_id": hashed_user_id,
                    "body_part": body_part,
                    "limit": limit
                })
                
                history = []
                for record in result:
                    history.append({
                        "id": record["id"],
                        "title": record["title"],
                        "description": record["description"],
                        "timestamp": record["timestamp"],
                        "severity": record["severity"],
                        "type": record["type"],
                        "confidence": record["confidence"],
                        "source": record["source"]
                    })
                
                return history
                
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
    
    def initialize_user_graph(self, user_id: str, patient_data: Dict[str, Any] = None) -> bool:
        """
        Initialize a complete user graph with patient node and patient-specific body parts.
        This is called automatically when a user first interacts with the system.
        """
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        try:
            from src.config.body_parts import get_default_body_parts
            
            hashed_user_id = self._hash_user_id(user_id)
            body_parts = get_default_body_parts()
            
            with self.driver.session() as session:
                # Create patient node
                patient_query = """
                MERGE (p:Patient {patient_id: $patient_id})
                SET p.user_id = $user_id,
                    p.age = $age,
                    p.gender = $gender,
                    p.created_at = $created_at,
                    p.updated_at = $updated_at,
                    p.initialized = true
                RETURN p
                """
                
                patient_data = patient_data or {}
                session.run(patient_query, {
                    "patient_id": hashed_user_id,
                    "user_id": hashed_user_id,
                    "age": patient_data.get("age"),
                    "gender": patient_data.get("gender"),
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                })
                
                # Create patient-specific body parts and connect them to the patient
                for body_part in body_parts:
                    body_part_query = """
                    MATCH (p:Patient {patient_id: $patient_id})
                    MERGE (b:BodyPart {name: $body_part_name, patient_id: $patient_id})
                    ON CREATE SET b.created_at = $created_at
                    MERGE (p)-[r:HAS_BODY_PART]->(b)
                    ON CREATE SET r.severity = 'NA', r.last_updated = $updated_at, r.event_count = 0
                    """
                    
                    session.run(body_part_query, {
                        "body_part_name": body_part,
                        "patient_id": hashed_user_id,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    })
                
                logger.info(f"User graph initialized for user {user_id[:8]}... with {len(body_parts)} patient-specific body parts")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize user graph: {e}")
            return False
    
    def is_user_initialized(self, user_id: str) -> bool:
        """Check if a user's graph has been initialized."""
        if not self._initialized:
            return False
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            with self.driver.session() as session:
                query = """
                MATCH (p:Patient {patient_id: $patient_id})
                RETURN p.initialized as initialized
                """
                
                result = session.run(query, {"patient_id": hashed_user_id})
                record = result.single()
                
                return record and record.get("initialized", False)
                
        except Exception as e:
            logger.error(f"Failed to check user initialization: {e}")
            return False
    
    def ensure_user_initialized(self, user_id: str, patient_data: Dict[str, Any] = None) -> bool:
        """
        Ensure a user's graph is initialized. If not, initialize it.
        This is the main function to call for automatic user initialization.
        """
        if not self.is_user_initialized(user_id):
            return self.initialize_user_graph(user_id, patient_data)
        return True
    
    def update_body_part_severities(self, user_id: str) -> bool:
        """Update severities for all body parts based on recent events."""
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        try:
            from src.config.body_parts import get_default_body_parts
            
            body_parts = get_default_body_parts()
            hashed_user_id = self._hash_user_id(user_id)
            
            with self.driver.session() as session:
                for body_part in body_parts:
                    # Calculate new severity based on events
                    new_severity = self.calculate_severity_from_events(user_id, body_part)
                    
                    # Update the severity
                    update_query = """
                    MATCH (p:Patient {patient_id: $patient_id})-[r:HAS_BODY_PART]->(b:BodyPart {name: $body_part, patient_id: $patient_id})
                    SET r.severity = $severity, r.last_updated = $updated_at
                    """
                    
                    session.run(update_query, {
                        "patient_id": hashed_user_id,
                        "body_part": body_part,
                        "severity": new_severity,
                        "updated_at": datetime.utcnow().isoformat()
                    })
            
            logger.info(f"Updated body part severities for user {user_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update body part severities: {e}")
            return False
    
    def get_body_part_severities(self, user_id: str) -> Dict[str, Any]:
        """Get current severity status for all body parts."""
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        try:
            from src.config.body_parts import get_default_body_parts
            
            hashed_user_id = self._hash_user_id(user_id)
            severities = {}
            
            with self.driver.session() as session:
                query = """
                MATCH (p:Patient {patient_id: $patient_id})-[r:HAS_BODY_PART]->(b:BodyPart {patient_id: $patient_id})
                RETURN b.name as body_part, 
                       coalesce(r.severity, 'NA') as severity,
                       coalesce(r.event_count, 0) as event_count,
                       r.last_updated as last_updated
                ORDER BY b.name
                """
                
                result = session.run(query, {"patient_id": hashed_user_id})
                
                for record in result:
                    severities[record["body_part"]] = {
                        "severity": record["severity"],
                        "event_count": record["event_count"],
                        "last_updated": record["last_updated"]
                    }
                
                # Ensure all default body parts are included
                default_parts = get_default_body_parts()
                for part in default_parts:
                    if part not in severities:
                        severities[part] = {
                            "severity": "NA",
                            "event_count": 0,
                            "last_updated": None
                        }
                
                return severities
                
        except Exception as e:
            logger.error(f"Failed to get body part severities: {e}")
            return {}
    
    def update_body_part_severity(self, user_id: str, body_part: str, severity: str) -> bool:
        """Update severity for a specific body part."""
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            with self.driver.session() as session:
                query = """
                MATCH (p:Patient {patient_id: $patient_id})-[r:HAS_BODY_PART]->(b:BodyPart {name: $body_part, patient_id: $patient_id})
                SET r.severity = $severity, r.last_updated = $updated_at
                RETURN r
                """
                
                result = session.run(query, {
                    "patient_id": hashed_user_id,
                    "body_part": body_part,
                    "severity": severity,
                    "updated_at": datetime.utcnow().isoformat()
                })
                
                # Check if update was successful
                return bool(result.single())
                
        except Exception as e:
            logger.error(f"Failed to update severity for {body_part}: {e}")
            return False

    def calculate_severity_from_events(self, user_id: str, body_part: str) -> str:
        """Calculate severity level for a body part based on recent events."""
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            with self.driver.session() as session:
                # Get recent events for this body part
                query = """
                MATCH (p:Patient {patient_id: $patient_id})-[:HAS_EVENT]->(e:Event)-[:AFFECTS]->(b:BodyPart {name: $body_part, patient_id: $patient_id})
                WHERE e.timestamp > date() - duration('P30D')  // Last 30 days
                RETURN e.severity as severity, e.timestamp as timestamp
                ORDER BY e.timestamp DESC
                LIMIT 10
                """
                
                result = session.run(query, {
                    "patient_id": hashed_user_id,
                    "body_part": body_part
                })
                
                events = list(result)
                
                if not events:
                    return "normal"
                
                # Simple severity calculation based on most recent and most severe events
                severities = [record["severity"] for record in events if record["severity"]]
                
                # Severity hierarchy
                severity_weights = {
                    "critical": 5,
                    "severe": 4,
                    "moderate": 3,
                    "mild": 2,
                    "normal": 1
                }
                
                # Get the highest severity from recent events
                max_weight = 1
                for severity in severities:
                    weight = severity_weights.get(severity.lower(), 1)
                    max_weight = max(max_weight, weight)
                
                # Map back to severity level
                for severity, weight in severity_weights.items():
                    if weight == max_weight:
                        return severity
                
                return "normal"
                
        except Exception as e:
            logger.error(f"Failed to calculate severity for {body_part}: {e}")
            return "normal"

    def list_patient_ids(self) -> List[str]:
        """List all patient IDs in the Neo4j database."""
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        try:
            with self.driver.session() as session:
                query = "MATCH (p:Patient) RETURN p.patient_id AS patient_id"
                result = session.run(query)
                return [record["patient_id"] for record in result]
                
        except Exception as e:
            logger.error(f"Failed to list patient IDs: {e}")
            return []

    def delete_user_data(self, user_id: str) -> bool:
        """Delete all data for a specific user from Neo4j."""
        if not self._initialized:
            raise RuntimeError("Neo4j not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            with self.driver.session() as session:
                # Delete the patient node and all connected nodes/relationships
                query = """
                MATCH (p:Patient {patient_id: $patient_id})
                OPTIONAL MATCH (p)-[*]-(connected)
                DETACH DELETE p, connected
                RETURN count(p) as deleted_count
                """
                
                result = session.run(query, {"patient_id": hashed_user_id})
                record = result.single()
                deleted_count = record["deleted_count"] if record else 0
                
                logger.info(f"Deleted Neo4j data for user {user_id[:8]}... (patient nodes: {deleted_count})")
                return deleted_count > 0
                
        except Exception as e:
            logger.error(f"Failed to delete user data from Neo4j: {e}")
            return False

    # ...existing code...
    

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
