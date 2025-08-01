"""
Document Processing Service
Handles background processing of uploaded medical documents

Features:
- Redis queue-based processing
- Medical text extraction and analysis
- Entity recognition and classification
- Neo4j knowledge graph integration
- Processing status tracking
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from src.core.config import settings
from src.db.mongodb import get_database
from src.db.redis_client import get_redis_client
from src.db.neo4j import neo4j_connection
from src.models.document import DocumentStatus

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Background document processing service"""
    
    def __init__(self):
        self.running = False
        self.mongodb = None
        self.redis = None
        self.neo4j = None
    
    async def initialize(self):
        """Initialize database connections"""
        try:
            from src.db.mongodb import mongodb
            if mongodb.database is not None:
                self.mongodb = mongodb.database
                logger.info("Document processor: MongoDB connected")
            
            self.redis = await get_redis_client()
            if self.redis is not None:
                logger.info("Document processor: Redis connected")
            
            if neo4j_connection.is_available():
                self.neo4j = neo4j_connection
                logger.info("Document processor: Neo4j connected")
            
            return True
        except Exception as e:
            logger.error(f"Document processor initialization failed: {e}")
            return False
    
    async def start_processing(self):
        """Start the background processing loop"""
        if not await self.initialize():
            logger.error("Cannot start document processor - initialization failed")
            return
        
        self.running = True
        logger.info("Document processor started")
        
        while self.running:
            try:
                # Process jobs from Redis queue
                await self.process_redis_queue()
                # Also process any pending documents directly
                await self.process_pending_documents()
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(30)  # Wait longer on error
    
    def stop_processing(self):
        """Stop the background processing"""
        self.running = False
        logger.info("Document processor stopped")
    
    async def process_redis_queue(self):
        """Process jobs from Redis queue"""
        if self.redis is None:
            return
        
        try:
            # Dequeue a job (non-blocking)
            job = await self.redis.dequeue_job(timeout=1)
            if job and job.get("job_type") == "document_processing":
                document_id = job.get("document_id")
                patient_id = job.get("patient_id")
                
                logger.info(f"Processing queued document: {document_id}")
                
                # Get document from MongoDB
                doc = await self.mongodb.documents.find_one({"document_id": document_id})
                if doc:
                    await self.process_single_document(doc)
                else:
                    logger.warning(f"Document not found in MongoDB: {document_id}")
                    
        except Exception as e:
            logger.error(f"Error processing Redis queue: {e}")
    
    async def process_pending_documents(self):
        """Process documents in pending status"""
        if self.mongodb is None:
            return
        
        try:
            # Find pending documents
            pending_docs = await self.mongodb.documents.find({
                "status": DocumentStatus.PENDING
            }).limit(5).to_list(5)
            
            for doc in pending_docs:
                await self.process_single_document(doc)
                
        except Exception as e:
            logger.error(f"Error processing pending documents: {e}")
    
    async def process_single_document(self, doc: Dict[str, Any]):
        """Process a single document"""
        document_id = doc["document_id"]
        
        try:
            logger.info(f"Processing document: {document_id}")
            
            # Update status to processing
            await self.mongodb.documents.update_one(
                {"document_id": document_id},
                {"$set": {"status": DocumentStatus.PROCESSING}}
            )
            
            # Use ingestion agent for proper processing
            from src.agents.ingestion_agent import IngestionAgent
            ingestion_agent = IngestionAgent()
            
            result = await ingestion_agent.process_document(
                patient_id=doc["patient_id"],
                document_id=document_id,
                file_path=doc["minio_path"],
                metadata=doc.get("metadata", {})
            )
            
            if result.get("success"):
                # Extract and format entities for health summary
                entities = result.get("entities", {})
                
                # Convert ingestion agent format to health summary format
                extracted_data_summary = {
                    "conditions": [],
                    "medications": [],
                    "symptoms": [],
                    "body_parts": [],
                    "procedures": []
                }
                
                # Process entities from ingestion agent format
                if isinstance(entities, dict):
                    # Extract conditions from diagnoses
                    for diagnosis in entities.get("diagnoses", []):
                        if isinstance(diagnosis, dict) and diagnosis.get("name"):
                            extracted_data_summary["conditions"].append(diagnosis["name"])
                    
                    # Extract treatments as medications/procedures
                    for treatment in entities.get("treatments", []):
                        if isinstance(treatment, dict) and treatment.get("name"):
                            treatment_name = treatment["name"]
                            # Simple classification - medication keywords
                            if any(keyword in treatment_name.lower() for keyword in ["mg", "tablet", "pill", "capsule", "dose", "daily", "medication"]):
                                extracted_data_summary["medications"].append(treatment_name)
                            else:
                                extracted_data_summary["procedures"].append(treatment_name)
                    
                    # Extract injury events as conditions
                    for injury in entities.get("injuryEvents", []):
                        if isinstance(injury, dict) and injury.get("name"):
                            extracted_data_summary["conditions"].append(injury["name"])
                    
                    # Extract notes for symptoms and body parts
                    for note in entities.get("notes", []):
                        if isinstance(note, dict) and note.get("text"):
                            note_text = note["text"].lower()
                            # Extract symptoms
                            symptom_keywords = ["pain", "ache", "fever", "nausea", "fatigue", "shortness of breath", "cough", "headache"]
                            for symptom in symptom_keywords:
                                if symptom in note_text:
                                    extracted_data_summary["symptoms"].append(symptom)
                            
                            # Extract body parts
                            body_part_keywords = ["heart", "lung", "chest", "head", "back", "knee", "shoulder", "stomach", "liver", "kidney"]
                            for body_part in body_part_keywords:
                                if body_part in note_text:
                                    extracted_data_summary["body_parts"].append(body_part)

                # Update document as completed with proper data format
                await self.mongodb.documents.update_one(
                    {"document_id": document_id},
                    {
                        "$set": {
                            "status": DocumentStatus.COMPLETED,
                            "processed_at": datetime.utcnow(),
                            "extracted_data_summary": extracted_data_summary,
                            "metadata.extracted_entities": entities,
                            "metadata.processing_time": datetime.utcnow()
                        }
                    }
                )
                logger.info(f"Document processed successfully: {document_id}")
            else:
                await self.mark_as_failed(document_id, result.get("error", "Unknown error"))
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            await self.mark_as_failed(document_id, str(e))
    
    async def read_document_content(self, file_path: str) -> Optional[str]:
        """Read content from document file"""
        try:
            if file_path.startswith("minio://"):
                # TODO: Implement MinIO file reading when available
                logger.warning("MinIO file reading not implemented yet")
                return None
            else:
                # Read from local file system
                path = Path(file_path)
                if path.exists():
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                else:
                    logger.error(f"File not found: {file_path}")
                    return None
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    async def extract_medical_entities(self, content: str) -> Dict[str, Any]:
        """Extract medical entities from document content"""
        # Simplified entity extraction - in production, use proper NLP models
        entities = {
            "conditions": [],
            "medications": [],
            "procedures": [],
            "body_parts": [],
            "symptoms": []
        }
        
        # Simple keyword matching (replace with proper NLP)
        content_lower = content.lower()
        
        # Common medical conditions
        conditions = ["hypertension", "diabetes", "heart disease", "cancer", "pneumonia", "asthma"]
        for condition in conditions:
            if condition in content_lower:
                entities["conditions"].append(condition)
        
        # Common medications
        medications = ["aspirin", "metformin", "lisinopril", "atorvastatin", "ibuprofen"]
        for med in medications:
            if med in content_lower:
                entities["medications"].append(med)
        
        # Body parts
        body_parts = ["heart", "lung", "kidney", "liver", "brain", "stomach"]
        for part in body_parts:
            if part in content_lower:
                entities["body_parts"].append(part)
        
        # Symptoms
        symptoms = ["pain", "fever", "cough", "fatigue", "nausea", "headache"]
        for symptom in symptoms:
            if symptom in content_lower:
                entities["symptoms"].append(symptom)
        
        return entities
    
    async def store_in_neo4j(self, doc: Dict[str, Any], entities: Dict[str, Any]):
        """Store extracted entities in Neo4j knowledge graph"""
        if self.neo4j is None:
            return
        
        try:
            patient_id = doc["patient_id"]
            document_id = doc["document_id"]
            
            # Create relationships for each entity type
            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    query = """
                    MATCH (p:Patient {patient_id: $patient_id})
                    MATCH (d:Document {document_id: $document_id})
                    MERGE (e:Entity {name: $entity, type: $entity_type})
                    MERGE (d)-[:CONTAINS]->(e)
                    MERGE (p)-[:HAS_CONDITION]->(e)
                    """
                    
                    self.neo4j.execute_query(query, {
                        "patient_id": patient_id,
                        "document_id": document_id,
                        "entity": entity,
                        "entity_type": entity_type
                    })
            
            logger.info(f"Stored entities in Neo4j for document: {document_id}")
            
        except Exception as e:
            logger.error(f"Error storing entities in Neo4j: {e}")
    
    async def mark_as_failed(self, document_id: str, error_message: str):
        """Mark document as failed with error message"""
        if self.mongodb is not None:
            await self.mongodb.documents.update_one(
                {"document_id": document_id},
                {
                    "$set": {
                        "status": DocumentStatus.FAILED,
                        "processed_at": datetime.utcnow(),
                        "error_message": error_message
                    }
                }
            )
            logger.error(f"Document marked as failed: {document_id} - {error_message}")

# Global processor instance
document_processor = DocumentProcessor()

async def start_document_processor():
    """Start the document processing service"""
    await document_processor.start_processing()

def stop_document_processor():
    """Stop the document processing service"""
    document_processor.stop_processing()
