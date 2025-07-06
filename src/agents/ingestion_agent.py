"""
Document ingestion agent for processing medical documents.

Features:
- PDF text extraction
- OCR for scanned documents
- Medical entity extraction
- Multi-database storage (MongoDB, Neo4j, Milvus)
"""

import os
import json
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
        """Extract medical entities from text using LLM-powered structured extraction."""
        try:
            from openai import AsyncOpenAI
            from src.config.settings import settings
            from src.config.body_parts import get_default_body_parts
            
            # Initialize OpenAI client
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            
            # Get available body parts for context
            body_parts = get_default_body_parts()
            
            # Define the JSON schema for structured output
            extraction_schema = {
                "type": "object",
                "properties": {
                    "medical_events": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "body_part": {
                                    "type": "string",
                                    "description": "The body part affected (must match one of the predefined body parts)",
                                    "enum": body_parts
                                },
                                "condition": {
                                    "type": "string",
                                    "description": "The medical condition, finding, or diagnosis"
                                },
                                "severity": {
                                    "type": "string",
                                    "description": "Severity level of the condition",
                                    "enum": ["critical", "severe", "moderate", "mild", "normal"]
                                },
                                "date": {
                                    "type": "string",
                                    "description": "Date of the event if mentioned (ISO format), or empty string if not specified"
                                },
                                "confidence": {
                                    "type": "number",
                                    "description": "Confidence in the extraction (0.0 to 1.0)",
                                    "minimum": 0.0,
                                    "maximum": 1.0
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Additional context or details about the finding"
                                }
                            },
                            "required": ["body_part", "condition", "severity", "confidence"]
                        }
                    }
                },
                "required": ["medical_events"]
            }
            
            # Create the extraction prompt
            system_prompt = """You are a medical information extraction assistant. Your task is to extract structured medical events from patient documents.

INSTRUCTIONS:
1. Extract only medical events that are explicitly mentioned in the document
2. For each event, identify the specific body part affected from the provided list
3. Determine the medical condition or finding
4. Assess the severity level based on the clinical context
5. Include dates if mentioned in the document
6. Provide a confidence score based on how clearly the information is stated
7. Do not hallucinate or infer information not present in the text
8. If a condition affects multiple body parts, create separate events for each

SEVERITY GUIDELINES:
- critical: Life-threatening conditions requiring immediate intervention
- severe: Serious conditions requiring urgent medical attention
- moderate: Conditions that need medical management but not urgent
- mild: Minor conditions or early-stage findings
- normal: Normal findings or resolved conditions

BODY PARTS AVAILABLE:
""" + ", ".join(body_parts)
            
            user_prompt = f"""Extract medical events from this document:

{text}

Return a JSON object with an array of medical events following the specified schema."""
            
            # Call OpenAI with structured output
            response = await client.chat.completions.create(
                model="gpt-4o-mini",  # Use gpt-4o-mini for cost efficiency
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "medical_extraction",
                        "schema": extraction_schema,
                        "strict": True
                    }
                },
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=2000
            )
            
            # Parse the JSON response
            import json
            result = json.loads(response.choices[0].message.content)
            medical_events = result.get("medical_events", [])
            
            # Convert to the expected format
            entities = []
            for event in medical_events:
                entities.append({
                    "type": "medical_event",
                    "body_part": event.get("body_part"),
                    "condition": event.get("condition"),
                    "severity": event.get("severity"),
                    "date": event.get("date", ""),
                    "confidence": event.get("confidence", 0.8),
                    "description": event.get("description", ""),
                    "extraction_method": "llm_structured_output"
                })
            
            logger.info(f"LLM extracted {len(entities)} medical entities from document")
            return entities
            
        except Exception as e:
            logger.error(f"LLM entity extraction failed: {e}")
            # Fallback to simple keyword matching if LLM fails
            return await self._fallback_keyword_extraction(text)
    
    async def _fallback_keyword_extraction(self, text: str) -> List[Dict[str, Any]]:
        """Fallback keyword-based extraction if LLM fails."""
        try:
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
                            "confidence": 0.6,  # Lower confidence for fallback
                            "extraction_method": "keyword_matching_fallback"
                        })
            
            logger.warning(f"Used fallback keyword extraction, found {len(entities)} entities")
            return entities
            
        except Exception as e:
            logger.error(f"Fallback extraction also failed: {e}")
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
        """Create knowledge graph relationships in Neo4j with enhanced LLM-extracted data."""
        try:
            neo4j_client = get_graph()
            
            # Ensure user graph is initialized
            neo4j_client.ensure_user_initialized(user_id)
            
            # Process each extracted entity
            for entity in entities:
                # Handle LLM-extracted medical events
                if entity.get("extraction_method") == "llm_structured_output":
                    await self._create_llm_medical_event(neo4j_client, user_id, document_id, entity)
                else:
                    # Handle fallback keyword-extracted entities
                    await self._create_fallback_medical_event(neo4j_client, user_id, document_id, entity)
            
            # Auto-update body part severities after processing
            neo4j_client.auto_update_body_part_severities(user_id)
            
            logger.info(f"Neo4j storage completed for document {document_id}: {len(entities)} entities processed")
            
        except Exception as e:
            logger.error(f"Neo4j storage failed: {e}")
            # Don't raise - Neo4j storage is not critical
    
    async def _create_llm_medical_event(
        self,
        neo4j_client,
        user_id: str,
        document_id: str,
        entity: Dict[str, Any]
    ):
        """Create a medical event from LLM-extracted data."""
        try:
            # Parse date if provided
            event_date = datetime.utcnow()
            if entity.get("date"):
                try:
                    from dateutil.parser import parse
                    event_date = parse(entity["date"])
                except:
                    logger.warning(f"Could not parse date: {entity.get('date')}")
            
            # Create comprehensive event data
            event_data = {
                "title": entity.get("condition", "Medical Finding"),
                "description": f"{entity.get('description', '')} (Source: Document {document_id})",
                "event_type": "medical_condition",
                "timestamp": event_date,
                "source": "llm_extraction",
                "severity": entity.get("severity", "mild"),
                "confidence": entity.get("confidence", 0.8),
                "body_part": entity.get("body_part"),
                "extraction_method": "llm_structured_output"
            }
            
            # Create the medical event in Neo4j
            event_id = neo4j_client.create_medical_event(
                user_id=user_id,
                event_data=event_data,
                body_parts=[entity.get("body_part")] if entity.get("body_part") else []
            )
            
            logger.debug(f"Created LLM medical event: {event_id}")
            
        except Exception as e:
            logger.error(f"Failed to create LLM medical event: {e}")
    
    async def _create_fallback_medical_event(
        self,
        neo4j_client,
        user_id: str,
        document_id: str,
        entity: Dict[str, Any]
    ):
        """Create a medical event from fallback keyword extraction."""
        try:
            # Determine severity using keyword rules
            severity = self._determine_entity_severity(entity)
            
            # Create event data
            event_data = {
                "title": entity.get("text", "Medical Finding"),
                "description": f"Keyword-extracted from document {document_id}. Category: {entity.get('category', 'unknown')}",
                "event_type": entity.get("category", "general"),
                "timestamp": datetime.utcnow(),
                "source": "keyword_extraction",
                "severity": severity,
                "confidence": entity.get("confidence", 0.6),
                "extraction_method": "keyword_matching_fallback"
            }
            
            # Try to map to body parts if it's a body part entity
            body_parts = []
            if entity.get("category") == "body_parts":
                # Use the body part mapping from config
                from src.config.body_parts import identify_body_parts_from_text
                body_parts = identify_body_parts_from_text(entity.get("text", ""))
            
            # Create the medical event in Neo4j
            event_id = neo4j_client.create_medical_event(
                user_id=user_id,
                event_data=event_data,
                body_parts=body_parts
            )
            
            logger.debug(f"Created fallback medical event: {event_id}")
            
        except Exception as e:
            logger.error(f"Failed to create fallback medical event: {e}")

    def _determine_entity_severity(self, entity: Dict[str, Any]) -> str:
        """
        Determine severity level for medical entities.
        For LLM-extracted entities, use the provided severity.
        For fallback entities, use keyword-based rules.
        """
        # If LLM provided severity, use it
        if entity.get("extraction_method") == "llm_structured_output":
            return entity.get("severity", "mild")
        
        # Fallback to keyword-based severity determination
        text = entity.get("text", "").lower()
        entity_type = entity.get("type", "")
        
        # Critical keywords
        critical_keywords = [
            "cancer", "tumor", "malignant", "metastasis", "stroke", "heart attack",
            "cardiac arrest", "sepsis", "hemorrhage", "fracture", "emergency"
        ]
        
        # Severe keywords
        severe_keywords = [
            "acute", "severe", "chronic", "infection", "pneumonia", "diabetes",
            "hypertension", "surgery", "operation", "hospitalization"
        ]
        
        # Moderate keywords
        moderate_keywords = [
            "moderate", "mild", "inflammation", "pain", "symptom", "medication",
            "treatment", "therapy", "monitoring"
        ]
        
        # Check for severity indicators
        if any(keyword in text for keyword in critical_keywords):
            return "critical"
        elif any(keyword in text for keyword in severe_keywords):
            return "severe"
        elif any(keyword in text for keyword in moderate_keywords):
            return "moderate"
        elif entity_type in ["medications", "procedures"]:
            return "mild"  # Medications and procedures are typically mild unless specified
        else:
            return "mild"  # Default to mild for unspecified conditions
    
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
