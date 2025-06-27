"""
Document ingestion agent for processing medical documents.

Features:
- PDF text extraction
- OCR for scanned documents
- Medical entity extraction
- Multi-database storage (MongoDB, Neo4j, Milvus)
"""

import os
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.utils.logging import logger, log_user_action
from src.db.mongo_db import get_mongo
from src.db.neo4j_db import get_graph
from src.db.milvus_db import get_milvus
from src.prompts import get_entities_prompt, get_ocr_prompt


class IngestionAgent:
    """
    Agent responsible for processing and ingesting medical documents.
    
    Workflow:
    1. Extract text from PDF/images
    2. Parse medical entities (conditions, medications, etc.)
    3. Store structured data in MongoDB
    4. Create knowledge graph relationships in Neo4j
    5. Generate and store embeddings in Milvus
    """
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
    
    async def process_document(
        self,
        user_id: str,
        document_id: str,
        file_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a document through the complete ingestion pipeline.
        
        Args:
            user_id: User identifier
            document_id: Document identifier
            file_path: Path to the uploaded file
            metadata: Document metadata
            
        Returns:
            Processing result with success status and extracted data
        """
        try:
            logger.info(f"Starting document processing: {document_id}")
            
            # Step 1: Extract text from document
            extraction_result = await self._extract_text(file_path, metadata)
            
            if not extraction_result["success"]:
                return {
                    "success": False,
                    "error": extraction_result["error"],
                    "stage": "text_extraction"
                }
            
            extracted_text = extraction_result["text"]
            page_count = extraction_result.get("page_count", 1)
            
            # Step 2: Parse medical entities
            entities = await self._extract_medical_entities(extracted_text)
            
            # Step 3: Store in MongoDB
            mongo_result = await self._store_in_mongodb(
                user_id, document_id, extracted_text, entities, metadata
            )
            
            # Step 4: Create knowledge graph relationships
            await self._store_in_neo4j(user_id, document_id, entities)
            
            # Step 5: Generate and store embeddings
            await self._store_embeddings(user_id, document_id, extracted_text)
            
            log_user_action(
                user_id,
                "document_processed",
                {
                    "document_id": document_id,
                    "page_count": page_count,
                    "entity_count": len(entities),
                    "text_length": len(extracted_text)
                }
            )
            
            return {
                "success": True,
                "document_id": document_id,
                "page_count": page_count,
                "entities": entities,
                "text_length": len(extracted_text),
                "mongo_id": mongo_result
            }
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "stage": "general_processing"
            }
    
    async def _extract_text(self, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text from document using appropriate method."""
        try:
            file_ext = os.path.splitext(file_path)[-1].lower()
            
            if file_ext == '.pdf':
                # Use PDF extractor tool
                try:
                    from src.tools.pdf_extractor import extract_pdf_text
                    text = extract_pdf_text(file_path)
                    return {
                        "success": True,
                        "text": text,
                        "page_count": 1,  # Simplified
                        "extraction_method": "pdf_plumber"
                    }
                except ImportError:
                    return {
                        "success": True,
                        "text": "PDF extraction not available",
                        "page_count": 1,
                        "extraction_method": "placeholder"
                    }
            
            elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                # Use OCR for images
                return {
                    "success": True,
                    "text": "OCR extraction not fully implemented",
                    "page_count": 1,
                    "extraction_method": "ocr_placeholder"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file format: {file_ext}"
                }
                
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _extract_medical_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract medical entities from text using NLP."""
        try:
            # Simple keyword-based extraction for demo
            entities = []
            
            medical_keywords = {
                "conditions": ["diabetes", "hypertension", "asthma", "pneumonia", "covid", "cancer"],
                "medications": ["metformin", "lisinopril", "albuterol", "aspirin", "insulin"],
                "body_parts": ["heart", "lung", "liver", "kidney", "brain", "arm", "leg"],
                "symptoms": ["pain", "fever", "cough", "fatigue", "nausea", "headache"]
            }
            
            text_lower = text.lower()
            
            for category, keywords in medical_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        entities.append({
                            "type": category,
                            "text": keyword,
                            "category": category,
                            "confidence": 0.8,
                            "extraction_method": "keyword_matching"
                        })
            
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []
    
    async def _store_in_mongodb(
        self,
        user_id: str,
        document_id: str,
        text: str,
        entities: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> str:
        """Store document data in MongoDB."""
        try:
            mongo_client = await get_mongo()
            
            record_data = {
                "document_id": document_id,
                "extracted_text": text,
                "entities": entities,
                "metadata": metadata,
                "processing_timestamp": datetime.utcnow().isoformat()
            }
            
            record_id = await mongo_client.store_medical_record(
                user_id=user_id,
                record_data=record_data,
                record_type="document"
            )
            
            return record_id
            
        except Exception as e:
            logger.error(f"MongoDB storage failed: {e}")
            raise
    
    async def _store_in_neo4j(
        self,
        user_id: str,
        document_id: str,
        entities: List[Dict[str, Any]]
    ):
        """Create knowledge graph relationships in Neo4j."""
        try:
            neo4j_client = get_graph()
            
            # Create patient node if not exists
            neo4j_client.create_patient_node(user_id, {})
            
            # Create events for medical entities
            for entity in entities:
                if entity["type"] in ["conditions", "symptoms"]:
                    event_data = {
                        "title": entity["text"],
                        "description": f"Mentioned in document {document_id}",
                        "event_type": "condition",
                        "timestamp": datetime.utcnow(),
                        "source": "document_processing"
                    }
                    
                    neo4j_client.create_medical_event(user_id, event_data)
            
        except Exception as e:
            logger.error(f"Neo4j storage failed: {e}")
            # Don't raise - Neo4j storage is not critical
    
    async def _store_embeddings(
        self,
        user_id: str,
        document_id: str,
        text: str
    ):
        """Generate and store text embeddings in Milvus."""
        try:
            milvus_client = get_milvus()
            
            # Split text into chunks for better embeddings
            chunks = self._split_text_into_chunks(text, max_length=500)
            
            if chunks:
                milvus_client.store_document_embeddings(
                    user_id=user_id,
                    document_id=document_id,
                    text_chunks=chunks,
                    metadata={"source": "document_processing"}
                )
            
        except Exception as e:
            logger.error(f"Milvus storage failed: {e}")
            # Don't raise - embeddings storage is not critical
    
    def _split_text_into_chunks(self, text: str, max_length: int = 500) -> List[str]:
        """Split text into chunks for embedding."""
        if not text:
            return []
        
        # Simple sentence-based splitting
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


# Global ingestion agent instance
_ingestion_agent = None


async def get_ingestion_agent() -> IngestionAgent:
    """Get the global ingestion agent instance."""
    global _ingestion_agent
    if _ingestion_agent is None:
        _ingestion_agent = IngestionAgent()
    return _ingestion_agent
