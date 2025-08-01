"""
Neo4j connection and operations
"""

import logging
import asyncio
import time
import uuid
from neo4j import GraphDatabase
from typing import Optional, List, Dict, Any

from src.core.config import settings
from src.core.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Neo4j database connection manager"""
    
    def __init__(self):
        self.driver = None
        self.uri = settings.NEO4J_URI
        # Use NEO4J_USER if available, fallback to NEO4J_USERNAME for compatibility
        self.username = getattr(settings, 'NEO4J_USER', settings.NEO4J_USERNAME)
        self.password = settings.NEO4J_PASSWORD
        # Delay actual connection until explicitly called
        self.driver = None
    
    def _connect(self):
        """Create connection to Neo4j with retry logic"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                if self.driver:
                    return
                    
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.username, self.password),
                    max_connection_pool_size=50,
                    connection_acquisition_timeout=30
                )
                
                # Verify connectivity with timeout
                with self.driver.session() as session:
                    session.run("RETURN 1", timeout=5)
                
                # Initialize schema
                self._initialize_schema()
                
                logger.info("Successfully connected to Neo4j")
                return
                
            except Exception as e:
                logger.warning(f"Neo4j connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if self.driver:
                    try:
                        self.driver.close()
                    except:
                        pass
                    self.driver = None
                    
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to connect to Neo4j after {max_retries} attempts: {e}")
                    # Don't raise exception to allow service to start in degraded mode
    
    def _initialize_schema(self):
        """Create constraints and indexes"""
        try:
            with self.driver.session() as session:
                # Constraints
                constraints = [
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.document_id IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE",
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (ev:Event) REQUIRE ev.event_id IS UNIQUE"
                ]
                
                for constraint in constraints:
                    try:
                        session.run(constraint)
                    except Exception as e:
                        logger.warning(f"Constraint might already exist: {e}")
                
                # Indexes
                indexes = [
                    "CREATE INDEX IF NOT EXISTS FOR (bp:BodyPart) ON (bp.name, bp.patient_id)",
                    "CREATE INDEX IF NOT EXISTS FOR (c:Condition) ON (c.name, c.patient_id)",
                    "CREATE INDEX IF NOT EXISTS FOR (t:Treatment) ON (t.name, t.patient_id)",
                    "CREATE INDEX IF NOT EXISTS FOR (e:Event) ON (e.date)",
                    "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.type)"
                ]
                
                for index in indexes:
                    try:
                        session.run(index)
                    except Exception as e:
                        logger.warning(f"Index might already exist: {e}")
                
                logger.info("Neo4j schema initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j schema: {e}")
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results"""
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def execute_write(self, query: str, parameters: Dict[str, Any] = None) -> Any:
        """Execute a write transaction"""
        try:
            with self.driver.session() as session:
                return session.execute_write(
                    lambda tx: tx.run(query, parameters or {}).consume()
                )
        except Exception as e:
            logger.error(f"Write transaction failed: {e}")
            raise
    
    def verify_connectivity(self) -> bool:
        """Verify database connectivity"""
        try:
            if not self.driver:
                return False
            with self.driver.session() as session:
                result = session.run("RETURN 1 as connected")
                return result.single()["connected"] == 1
        except:
            return False
            
    def is_available(self) -> bool:
        """Check if Neo4j is available"""
        return self.driver is not None
    
    async def connect(self):
        """Async wrapper to initialize connection"""
        self._connect()

    async def close(self):
        """Close database connection"""
        if self.driver:
            if self.driver:
                self.driver.close()
                self.driver = None
            logger.info("Neo4j connection closed")
    
    # Patient-specific operations
    def create_patient_if_not_exists(self, patient_id: str) -> None:
        """Create patient node if it doesn't exist"""
        query = """
        MERGE (p:Patient {patient_id: $patient_id})
        ON CREATE SET p.created_at = datetime()
        ON MATCH SET p.last_accessed = datetime()
        """
        self.execute_write(query, {"patient_id": patient_id})
    
    def get_patient_body_parts(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get all body parts for a patient"""
        query = """
        MATCH (p:Patient {patient_id: $patient_id})-[:HAS_BODY_PART]->(bp:BodyPart)
        RETURN bp
        ORDER BY bp.severity DESC
        """
        return self.execute_query(query, {"patient_id": patient_id})
    
    def update_body_part_severity(self, patient_id: str, body_part: str, severity: float) -> None:
        """Update body part severity"""
        query = """
        MATCH (p:Patient {patient_id: $patient_id})
        MERGE (bp:BodyPart {name: $body_part, patient_id: $patient_id})
        SET bp.severity = $severity,
            bp.last_updated = datetime()
        MERGE (p)-[:HAS_BODY_PART]->(bp)
        """
        self.execute_write(query, {
            "patient_id": patient_id,
            "body_part": body_part,
            "severity": severity
        })
    
    def get_patient_timeline(self, patient_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get patient timeline events"""
        query = """
        MATCH (p:Patient {patient_id: $patient_id})-[:HAS_EVENT]->(e:Event)
        RETURN e
        ORDER BY e.date DESC
        LIMIT $limit
        """
        return self.execute_query(query, {"patient_id": patient_id, "limit": limit})
    
    def create_constraints(self):
        """Create Neo4j constraints and indexes for HIPAA-compliant patient isolation"""
        constraints = [
            "CREATE CONSTRAINT patient_id_unique IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE",
            "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.document_id IS UNIQUE",
            # HIPAA COMPLIANCE: Use composite constraint for patient isolation
            "CREATE CONSTRAINT body_part_patient_unique IF NOT EXISTS FOR (bp:BodyPart) REQUIRE (bp.name, bp.patient_id) IS UNIQUE",
            "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE",
            "CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (ev:Event) REQUIRE ev.event_id IS UNIQUE",
            # Add patient isolation constraints for other entity types
            "CREATE CONSTRAINT condition_patient_unique IF NOT EXISTS FOR (c:Condition) REQUIRE (c.name, c.patient_id) IS UNIQUE",
            "CREATE CONSTRAINT treatment_patient_unique IF NOT EXISTS FOR (t:Treatment) REQUIRE (t.name, t.patient_id) IS UNIQUE"
        ]
        
        indexes = [
            "CREATE INDEX patient_created_at IF NOT EXISTS FOR (p:Patient) ON (p.created_at)",
            "CREATE INDEX document_uploaded_at IF NOT EXISTS FOR (d:Document) ON (d.uploaded_at)",
            "CREATE INDEX entity_date IF NOT EXISTS FOR (e:Entity) ON (e.date)",
            "CREATE INDEX event_date IF NOT EXISTS FOR (ev:Event) ON (ev.date)",
            "CREATE INDEX entity_severity IF NOT EXISTS FOR (e:Entity) ON (e.severity)"
        ]
        
        try:
            for constraint in constraints:
                self.execute_query(constraint)
            
            for index in indexes:
                self.execute_query(index)
            
            logger.info("Neo4j constraints and indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Failed to create some constraints/indexes: {e}")
    
    def create_patient_graph(self, patient_id: str) -> bool:
        """Create initial patient graph structure"""
        try:
            query = """
            MERGE (p:Patient {patient_id: $patient_id})
            ON CREATE SET p.created_at = datetime()
            ON MATCH SET p.updated_at = datetime()
            
            // Create body part nodes with HIPAA-compliant patient isolation
            WITH p
            UNWIND $body_parts AS body_part
            MERGE (bp:BodyPart {name: body_part, patient_id: $patient_id})
            SET bp.created_at = CASE WHEN bp.created_at IS NULL THEN datetime() ELSE bp.created_at END
            MERGE (p)-[:HAS_BODY_PART]->(bp)
            
            RETURN p.patient_id as patient_id
            """
            
            self.execute_write(query, {
                "patient_id": patient_id,
                "body_parts": settings.BODY_PARTS
            })
            return True
            
        except Exception as e:
            logger.error(f"Failed to create patient graph: {e}")
            return False
    
    def add_document_to_graph(self, document_id: str, patient_id: str, filename: str) -> bool:
        """Add document node to patient graph with HIPAA-compliant patient isolation"""
        try:
            query = """
            MATCH (p:Patient {patient_id: $patient_id})
            CREATE (d:Document {
                document_id: $document_id,
                patient_id: $patient_id,
                filename: $filename,
                uploaded_at: datetime()
            })
            CREATE (p)-[:HAS_DOCUMENT]->(d)
            RETURN d.document_id as document_id
            """
            
            self.execute_write(query, {
                "patient_id": patient_id,
                "document_id": document_id,
                "filename": filename
            })

            return True
            
        except Exception as e:
            logger.error(f"Failed to add document to graph: {e}")
            return False

    def create_event_node(self, event_data: Dict[str, Any], patient_id: str) -> str:
        """Create an event node in Neo4j with HIPAA-compliant patient isolation"""
        try:
            event_id = f"event_{patient_id}_{uuid.uuid4().hex[:8]}"  # Include patient_id in event_id
            query = """
            CREATE (e:Event {
                event_id: $event_id,
                patient_id: $patient_id,
                type: $type,
                description: $description,
                date: $date,
                severity: $severity,
                created_at: datetime()
            })
            RETURN e.event_id as event_id
            """
            
            parameters = {
                "event_id": event_id,
                "patient_id": patient_id,  # Ensure patient isolation
                "type": event_data.get("type", "unknown"),
                "description": event_data.get("description", ""),
                "date": event_data.get("date", ""),
                "severity": event_data.get("severity", 0)
            }
            
            result = self.execute_write(query, parameters)
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to create event node: {e}")
            return None

    def create_relationships(self, patient_id: str, document_id: str, event_type: str, event_id: str) -> bool:
        """Create relationships between patient, document, and event with HIPAA compliance validation"""
        try:
            # HIPAA COMPLIANCE: Ensure all entities belong to the same patient
            query = """
            MATCH (p:Patient {patient_id: $patient_id})
            MATCH (d:Document {document_id: $document_id, patient_id: $patient_id})
            MATCH (e:Event {event_id: $event_id, patient_id: $patient_id})
            
            // Validate patient isolation - all entities must belong to the same patient
            WITH p, d, e
            WHERE p.patient_id = d.patient_id AND p.patient_id = e.patient_id
            
            CREATE (p)-[:HAS_EVENT]->(e)
            CREATE (d)-[:CONTAINS_EVENT]->(e)
            
            RETURN e.event_id as event_id
            """
            
            result = self.execute_write(query, {
                "patient_id": patient_id,
                "document_id": document_id,
                "event_id": event_id
            })
            
            if not result:
                logger.warning(f"HIPAA VIOLATION PREVENTED: Attempted to link entities from different patients. Patient: {patient_id}, Document: {document_id}, Event: {event_id}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create relationships: {e}")
            return False


    def validate_patient_isolation(self, patient_id: str) -> Dict[str, Any]:
        """
        HIPAA COMPLIANCE: Validate that patient data is properly isolated
        Returns audit report of any cross-patient data leaks
        """
        try:
            query = """
            // Check for body parts without patient_id or belonging to wrong patient
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_BODY_PART]->(bp:BodyPart)
            WHERE bp.patient_id IS NULL OR bp.patient_id <> $patient_id
            WITH COUNT(bp) as orphaned_body_parts
            
            // Check for events without patient_id or belonging to wrong patient
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_EVENT]->(e:Event)
            WHERE e.patient_id IS NULL OR e.patient_id <> $patient_id
            WITH orphaned_body_parts, COUNT(e) as orphaned_events
            
            // Check for conditions without patient_id or belonging to wrong patient
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_CONDITION]->(c:Condition)
            WHERE c.patient_id IS NULL OR c.patient_id <> $patient_id
            WITH orphaned_body_parts, orphaned_events, COUNT(c) as orphaned_conditions
            
            RETURN {
                patient_id: $patient_id,
                orphaned_body_parts: orphaned_body_parts,
                orphaned_events: orphaned_events,
                orphaned_conditions: orphaned_conditions,
                is_hipaa_compliant: orphaned_body_parts = 0 AND orphaned_events = 0 AND orphaned_conditions = 0
            } as audit_result
            """
            
            result = self.execute_query(query, {"patient_id": patient_id})
            return result[0]["audit_result"] if result else {}
            
        except Exception as e:
            logger.error(f"Failed to validate patient isolation: {e}")
            return {"error": str(e), "is_hipaa_compliant": False}

    def fix_patient_data_isolation(self, patient_id: str) -> bool:
        """
        HIPAA COMPLIANCE: Fix any data isolation issues for a patient
        This should be run after identifying isolation problems
        """
        try:
            query = """
            // Fix body parts - add missing patient_id
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_BODY_PART]->(bp:BodyPart)
            WHERE bp.patient_id IS NULL
            SET bp.patient_id = $patient_id
            
            WITH COUNT(*) as fixed_body_parts
            
            // Fix events - add missing patient_id
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_EVENT]->(e:Event)
            WHERE e.patient_id IS NULL
            SET e.patient_id = $patient_id
            
            WITH fixed_body_parts, COUNT(*) as fixed_events
            
            // Fix conditions - add missing patient_id
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_CONDITION]->(c:Condition)
            WHERE c.patient_id IS NULL
            SET c.patient_id = $patient_id
            
            RETURN {
                fixed_body_parts: fixed_body_parts,
                fixed_events: fixed_events,
                fixed_conditions: COUNT(*)
            } as fix_result
            """
            
            result = self.execute_write(query, {"patient_id": patient_id})
            logger.info(f"HIPAA compliance fix applied for patient {patient_id}: {result}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fix patient data isolation: {e}")
            return False


# Global Neo4j connection instance
neo4j_connection = Neo4jConnection()

