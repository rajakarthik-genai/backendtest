"""
Neo4j connection and operations
"""

import logging
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
        self.username = settings.NEO4J_USERNAME
        self.password = settings.NEO4J_PASSWORD
        # Delay actual connection until explicitly called
        self.driver = None
    
    def _connect(self):
        """Create connection to Neo4j"""
        try:
            if self.driver:
                return
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_pool_size=50,
                connection_acquisition_timeout=30
            )
            
            # Verify connectivity
            with self.driver.session() as session:
                session.run("RETURN 1")
            
            # Initialize schema
            self._initialize_schema()
            
            logger.info("Successfully connected to Neo4j")
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
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
            with self.driver.session() as session:
                result = session.run("RETURN 1 as connected")
                return result.single()["connected"] == 1
        except:
            return False
    
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
        """Create Neo4j constraints and indexes"""
        constraints = [
            "CREATE CONSTRAINT patient_id_unique IF NOT EXISTS FOR (p:Patient) REQUIRE p.patient_id IS UNIQUE",
            "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.document_id IS UNIQUE",
            "CREATE CONSTRAINT body_part_name_unique IF NOT EXISTS FOR (bp:BodyPart) REQUIRE bp.name IS UNIQUE",
            "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE",
            "CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (ev:Event) REQUIRE ev.event_id IS UNIQUE"
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
            
            // Create body part nodes
            WITH p
            UNWIND $body_parts AS body_part
            MERGE (bp:BodyPart {name: body_part})
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
        """Add document node to patient graph"""
        try:
            query = """
            MATCH (p:Patient {patient_id: $patient_id})
            CREATE (d:Document {
                document_id: $document_id,
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


# Global Neo4j connection instance
neo4j_connection = Neo4jConnection()

