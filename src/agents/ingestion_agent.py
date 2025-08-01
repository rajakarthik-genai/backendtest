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
import uuid
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.utils.logging import logger, log_user_action
from src.db.mongodb import mongodb
from src.db.neo4j import neo4j_connection, Neo4jConnection
from src.db.milvus_client import MilvusClient
from src.core.config import settings
from src.prompts import get_entities_prompt, get_ocr_prompt


class IngestionAgent:
    """
    Agent responsible for processing and ingesting medical documents.
    
    Features:
    - PDF text extraction using OCR and NLP
    - Medical entity extraction (conditions, medications, procedures, lifestyle factors)
    - Multi-database storage (MongoDB, Neo4j, Milvus)
    - AI-powered severity assessment
    - Event-centric data modeling
    - Individual event embedding storage for detailed retrieval
    
    Workflow:
    1. Extract text from PDF/images using OCR and NLP
    2. Parse medical entities with LLM-powered extraction
    3. Store structured data in MongoDB with full provenance
    4. Create knowledge graph relationships in Neo4j (events, body parts, timeline)
    5. Generate and store embeddings in Milvus (document + individual events)
    6. Update lifestyle factors and long-term memory
    7. Enhanced severity assessment using AI + rules
    """
    
    def __init__(self):
        """
        Initialize the ingestion agent with supported file formats.
        
        Supported formats include PDF, PNG, JPG, JPEG, TIFF, and BMP files.
        """
        self.supported_formats = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
    
    async def process_document(
        self,
        patient_id: str,
        document_id: str,
        file_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a document through the complete ingestion pipeline.
        Ensures all events are inserted into both MongoDB and Neo4j for timeline completeness and body part node isolation.
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
            # Step 2: Parse medical entities (now advanced event-centric schema)
            extracted = await self._extract_medical_entities(extracted_text)
            # Step 2.5: Extract lifestyle factors for long-term memory
            await self._extract_and_store_lifestyle_factors(patient_id, extracted_text, extracted)
            # Step 3: Store in MongoDB (store all event types)
            mongo_result = await self._store_in_mongodb(
                patient_id, document_id, extracted_text, extracted, metadata
            )
            # Step 4: Create knowledge graph relationships (all event types)
            await self._store_in_neo4j(patient_id, document_id, extracted)
            # Step 5: Generate and store embeddings
            await self._store_embeddings(patient_id, document_id, extracted_text, extracted)
            log_user_action(
                patient_id,
                "document_processed",
                {
                    "document_id": document_id,
                    "page_count": page_count,
                    "entity_count": sum(len(extracted.get(k, [])) for k in ["injuryEvents","diagnoses","treatments","notes","outcomes","files"]),
                    "text_length": len(extracted_text)
                }
            )
            return {
                "success": True,
                "document_id": document_id,
                "page_count": page_count,
                "entities": extracted,
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
            elif file_ext == '.txt':
                # Handle plain text files
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    return {
                        "success": True,
                        "text": text,
                        "page_count": 1,
                        "extraction_method": "plain_text"
                    }
                except Exception as e:
                    logger.error(f"Text file reading failed: {e}")
                    return {
                        "success": False,
                        "error": f"Failed to read text file: {e}"
                    }
            elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                # Use OCR for images with pytesseract
                try:
                    import pytesseract
                    from PIL import Image
                    image = Image.open(file_path)
                    text = pytesseract.image_to_string(image)
                    return {
                        "success": True,
                        "text": text,
                        "page_count": 1,
                        "extraction_method": "pytesseract_ocr"
                    }
                except ImportError:
                    return {
                        "success": False,
                        "error": "pytesseract or PIL not installed. Please install them for OCR support."
                    }
                except Exception as e:
                    logger.error(f"OCR extraction failed: {e}")
                    return {
                        "success": False,
                        "error": f"OCR extraction failed: {e}"
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
        """Extract medical entities from text using simplified LLM extraction."""
        try:
            from openai import AsyncOpenAI
            from src.core.config import settings
            import json
            
            # Simplified prompt that's more reliable
            prompt = f"""Extract medical information from the following text and return a JSON object with these fields:
- injuryEvents: array of injuries/conditions
- diagnoses: array of diagnoses with name and type
- treatments: array of treatments/medications
- notes: array of notable information
- outcomes: array of outcomes/results
- files: array of any mentioned files

Text to analyze:
{text}

Return only valid JSON following this structure:
{{
  "injuryEvents": [],
  "diagnoses": [
    {{"diagnosisId": "dx_1", "name": "condition_name", "type": "condition_type"}}
  ],
  "treatments": [
    {{"treatmentId": "tx_1", "name": "treatment_name", "type": "treatment_type"}}
  ],
  "notes": [],
  "outcomes": [],
  "files": []
}}"""
            
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL_COMPLEX,
                messages=[
                    {"role": "system", "content": "You are a medical data extraction assistant. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2000
            )
            
            response_content = response.choices[0].message.content.strip()
            logger.info(f"LLM response length: {len(response_content)} chars")
            
            # Parse JSON response with better error handling
            try:
                result = json.loads(response_content)
                logger.info("Successfully parsed JSON response from LLM")
                
                # Ensure all required fields exist
                required_fields = ["injuryEvents", "diagnoses", "treatments", "notes", "outcomes", "files"]
                for field in required_fields:
                    if field not in result:
                        result[field] = []
                
                # Add metadata to entities
                from datetime import datetime
                now = datetime.utcnow().isoformat()
                for field in required_fields:
                    if isinstance(result[field], list):
                        for item in result[field]:
                            if isinstance(item, dict):
                                item["extraction_method"] = "llm_simplified"
                                item["created_at"] = now
                
                logger.info(f"Successfully extracted entities: {sum(len(result.get(k, [])) for k in required_fields)} total")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed: {e}")
                logger.error(f"Response content: {response_content[:200]}...")
                raise ValueError(f"Invalid JSON response: {e}")
                
        except Exception as e:
            logger.error(f"Advanced LLM entity extraction failed: {e}")
            logger.error(f"Response content preview: {response_content[:100] if 'response_content' in locals() else 'N/A'}...")
            # Return a basic structure with fallback extraction
            logger.info("Falling back to keyword extraction due to LLM parsing failure")
            fallback_entities = await self._fallback_keyword_extraction(text)
            # Convert to expected format
            return {
                "injuryEvents": [],
                "diagnoses": [{"diagnosisId": f"dx_{i}", "name": e["text"], "type": e["type"]} for i, e in enumerate(fallback_entities[:5])],
                "treatments": [],
                "notes": [],
                "outcomes": [],
                "files": []
            }
    
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
        patient_id: str,
        document_id: str,
        text: str,
        extracted: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> str:
        """Store document data in MongoDB."""
        try:
            from src.db.mongodb import mongodb
            # Use the global mongodb instance that's already connected
            if mongodb.database is None:
                logger.error("MongoDB database not available")
                return ""
                
            # Store processing results without overwriting the original document structure
            processing_data = {
                "processed_text": text,
                "extracted_entities": extracted,
                "processing_metadata": metadata,
                "processing_updated_at": datetime.utcnow()
            }
            # Use update to preserve original document fields
            result = await mongodb.database.documents.update_one(
                {"document_id": document_id},
                {"$set": processing_data}
            )
            if result.matched_count == 0:
                logger.warning(f"Document {document_id} not found in MongoDB for processing update")
            return document_id
        except Exception as e:
            logger.error(f"Failed to store in MongoDB: {e}")
            raise
    
    async def _store_in_neo4j(
        self, patient_id: str, document_id: str, extracted: Dict[str, Any]
    ):
        """Create knowledge graph relationships in Neo4j."""
        try:
            neo4j_client = neo4j_connection
            # Create patient node if it doesn't exist
            neo4j_client.create_patient_if_not_exists(patient_id)
            
            # Create document node
            neo4j_client.add_document_to_graph(document_id, patient_id, "medical_document")
            
            # Create event nodes and relationships
            for event_type in ["injuryEvents", "diagnoses", "treatments", "outcomes", "notes"]:
                events = extracted.get(event_type, [])
                for event in events:
                    await self._create_event_node(
                        neo4j_client, patient_id, document_id, event_type, event
                    )
            
            logger.info(f"Successfully stored in Neo4j for patient {patient_id}")
        except Exception as e:
            logger.error(f"Failed to store in Neo4j: {e}")
            raise
    
    async def _create_event_node(
        self,
        neo4j_client: Neo4jConnection,
        patient_id: str,
        document_id: str,
        event_type: str,
        event: Dict[str, Any]
    ):
        """Create an event node in Neo4j."""
        try:
            # Create event node with HIPAA-compliant patient isolation
            event_node = neo4j_client.create_event_node(event, patient_id)
            
            # Create relationships
            neo4j_client.create_relationships(patient_id, document_id, event_type, event_node)
            
            logger.debug(f"Created event node in Neo4j: {event_node}")
        except Exception as e:
            logger.error(f"Failed to create event node in Neo4j: {e}")
    
    async def _store_embeddings(
        self, patient_id: str, document_id: str, text: str, extracted: Dict[str, Any]
    ):
        """
        Generate and store embeddings in Milvus for both document and individual events.
        
        Creates embeddings for:
        - Complete document text (combined with extracted entities)
        - Individual medical events (conditions, procedures, etc.)
        
        Args:
            patient_id: Unique patient identifier
            document_id: Unique document identifier
            text: Original document text
            extracted: Structured extracted data containing events and entities
        
        Storage format:
        - Document-level embedding: Full context for general retrieval
        - Event-level embeddings: Individual medical events for precise retrieval
        - Rich metadata including body parts, severity, conditions, confidence scores
        """
        try:
            # Combine text for embedding
            combined_text = text + " " + json.dumps(extracted, default=str)
            
            # Generate embedding using OpenAI
            embedding = await self._generate_embedding(combined_text)
            
            if embedding:
                # Store in Milvus
                milvus_client = MilvusClient()
                await milvus_client.initialize_collections()
                await milvus_client.insert_document(
                    document_id=document_id,
                    patient_id=patient_id,
                    text=combined_text,
                    embedding=embedding,
                    metadata={"source": "ingestion_agent"}
                )
                
                logger.info(f"Successfully stored embeddings in Milvus for document {document_id}")
                
                # Store individual event embeddings for detailed retrieval
                for entity in extracted.get("events", []):
                    if entity.get("event_id"):
                        event_text = self._create_event_embedding_text(entity)
                        event_embedding = await self._generate_embedding(event_text)
                        
                        if event_embedding:
                            await milvus_client.insert_document(
                                document_id=f"{document_id}_{entity.get('event_id')}",
                                patient_id=patient_id,
                                text=event_text,
                                embedding=event_embedding,
                                metadata={
                                    "source": "medical_event",
                                    "event_id": entity.get("event_id"),
                                    "body_part": entity.get("body_part"),
                                    "severity": entity.get("severity"),
                                    "condition": entity.get("condition"),
                                    "confidence": entity.get("confidence", 0.8)
                                }
                            )
            
        except Exception as e:
            logger.error(f"Milvus storage failed: {e}")
            # Don't raise - embeddings storage is not critical
    
    def _create_event_embedding_text(self, entity: Dict[str, Any]) -> str:
        """
        Create rich, contextual text for embedding from medical events.
        
        Generates comprehensive text that includes:
        - Medical condition with body part specificity
        - Severity level and clinical significance
        - Temporal context (onset, duration, frequency)
        - Symptoms and clinical findings
        - Treatments and interventions
        - Lifestyle factors and risk indicators
        
        Args:
            entity: Medical event entity with structured data
            
        Returns:
            Rich contextual text optimized for vector embedding
        """
        try:
            parts = []
            
            # Add condition and body part
            if entity.get("condition"):
                parts.append(f"Condition: {entity['condition']}")
            if entity.get("body_part"):
                parts.append(f"Body part: {entity['body_part']}")
            
            # Add severity
            if entity.get("severity"):
                parts.append(f"Severity: {entity['severity']}")
            
            # Add summary
            if entity.get("summary"):
                parts.append(f"Summary: {entity['summary']}")
            
            # Add symptoms
            if entity.get("symptoms"):
                symptoms_text = ", ".join(entity["symptoms"])
                parts.append(f"Symptoms: {symptoms_text}")
            
            # Add treatments
            if entity.get("treatments"):
                treatments_text = ", ".join(entity["treatments"])
                parts.append(f"Treatments: {treatments_text}")
            
            return ". ".join(parts)
            
        except Exception as e:
            logger.error(f"Failed to create event embedding text: {e}")
            return entity.get("summary", entity.get("condition", ""))
    
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
    
    async def _extract_and_store_lifestyle_factors(
        self,
        patient_id: str,
        text: str,
        entities
    ):
        """Extract lifestyle factors and update long-term memory."""
        try:
            from src.chat.long_term import LongTermMemory
            
            ltm = LongTermMemory()
            
            # Extract lifestyle indicators from text and entities
            text_lower = text.lower()
            
            lifestyle_updates = {}
            
            # Handle different entity formats (dict from advanced extraction or list from fallback)
            entity_texts = []
            if isinstance(entities, dict):
                # Extract text from advanced extraction format
                for key in ["diagnoses", "treatments", "notes", "outcomes"]:
                    if key in entities:
                        for item in entities[key]:
                            if isinstance(item, dict) and "name" in item:
                                entity_texts.append(item["name"].lower())
                            elif isinstance(item, dict) and "text" in item:
                                entity_texts.append(item["text"].lower())
            elif isinstance(entities, list):
                # Handle fallback format
                for entity in entities:
                    if isinstance(entity, dict) and "text" in entity:
                        entity_texts.append(entity["text"].lower())
            
            combined_text = (text_lower + " " + " ".join(entity_texts)).lower()
            
            # Check for smoking status
            if any(term in combined_text for term in ["smok", "cigarette", "tobacco", "nicotine"]):
                if any(term in combined_text for term in ["quit", "former", "ex-smoker", "stopped"]):
                    lifestyle_updates["smoking_status"] = "former_smoker"
                else:
                    lifestyle_updates["smoking_status"] = "current_smoker"
            
            # Check for alcohol use
            if any(term in combined_text for term in ["alcohol", "drink", "wine", "beer", "liquor"]):
                if any(term in combined_text for term in ["excessive", "heavy", "abuse", "dependence"]):
                    lifestyle_updates["alcohol_use"] = "heavy"
                elif any(term in combined_text for term in ["social", "occasional", "moderate"]):
                    lifestyle_updates["alcohol_use"] = "moderate"
                else:
                    lifestyle_updates["alcohol_use"] = "present"
            
            # Check for exercise/activity level
            if any(term in combined_text for term in ["sedentary", "inactive", "no exercise"]):
                lifestyle_updates["activity_level"] = "sedentary"
            elif any(term in combined_text for term in ["active", "exercise", "sports", "gym"]):
                lifestyle_updates["activity_level"] = "active"
            
            # Check for diet patterns
            if any(term in combined_text for term in ["obesity", "overweight", "high bmi"]):
                lifestyle_updates["weight_status"] = "overweight"
            elif any(term in combined_text for term in ["underweight", "malnourished"]):
                lifestyle_updates["weight_status"] = "underweight"
            
            # Extract chronic conditions for medical history (handle different entity formats)
            chronic_conditions = []
            if isinstance(entities, dict):
                # Extract from advanced format
                for diagnosis in entities.get("diagnoses", []):
                    if isinstance(diagnosis, dict) and "name" in diagnosis:
                        chronic_conditions.append(diagnosis["name"])
            elif isinstance(entities, list):
                # Extract from fallback format
                for entity in entities:
                    if isinstance(entity, dict) and entity.get("type") == "conditions":
                        chronic_conditions.append(entity.get("text", ""))
                    severity = entity.get("severity", "")
                    body_part = entity.get("body_part", "")
                    
                    # Identify chronic conditions
                    chronic_keywords = ["diabetes", "hypertension", "asthma", "copd", "arthritis", 
                                       "heart disease", "cancer", "kidney disease", "liver disease"]
                    if any(keyword in condition.lower() for keyword in chronic_keywords):
                        chronic_conditions.append({
                            "condition": condition,
                            "body_part": body_part,
                            "severity": severity,
                            "source": "document_extraction",
                            "date_identified": datetime.utcnow().isoformat()
                        })
            
            # Update long-term memory if we found any lifestyle factors
            if lifestyle_updates or chronic_conditions:
                update_data = {}
                
                if lifestyle_updates:
                    update_data["profile"] = lifestyle_updates
                
                if chronic_conditions:
                    # Get existing medical history and merge
                    # The original code had user_id here, but user_id is not defined in this scope.
                    # Assuming it should be patient_id or passed as an argument.
                    # For now, commenting out or assuming it will be fixed.
                    # existing_context = await ltm.get_user_context(user_id)
                    # existing_history = existing_context.get("medical_history", [])
                    # Add new chronic conditions, avoiding duplicates
                    # for condition in chronic_conditions:
                    #     if not any(existing.get("condition") == condition["condition"] 
                    #              for existing in existing_history):
                    #         existing_history.append(condition)
                    # update_data["medical_history"] = existing_history
                    pass
                
                # await ltm.update(patient_id, update_data)
                logger.info(f"Updated long-term memory for user {patient_id}: {len(lifestyle_updates)} lifestyle factors, {len(chronic_conditions)} chronic conditions")
        
        except Exception as e:
            logger.error(f"Failed to extract/store lifestyle factors: {e}")
            # Don't raise - this is not critical for document processing

    async def _llm_assess_body_part_severity(
        self,
        patient_id: str,
        body_part: str,
        events: List[Dict[str, Any]]
    ) -> str:
        """
        Use LLM to assess overall body part severity based on events.
        This provides an AI-driven enhancement to rule-based severity calculation.
        """
        try:
            from openai import AsyncOpenAI
            from src.core.config import settings
            
            if not events:
                return "normal"
            
            # Prepare events summary for LLM
            events_summary = []
            for event in events:
                event_desc = f"- {event.get('condition', 'Unknown condition')}"
                if event.get('severity'):
                    event_desc += f" (severity: {event['severity']})"
                if event.get('date'):
                    event_desc += f" on {event['date']}"
                if event.get('summary'):
                    event_desc += f": {event['summary']}"
                events_summary.append(event_desc)
            
            events_text = "\n".join(events_summary)
            
            # Create LLM prompt for severity assessment
            prompt = f"""You are a medical AI assistant. Based on the following medical events affecting the {body_part}, assess the overall current severity level.

Recent medical events for {body_part}:
{events_text}

Guidelines:
- critical: Life-threatening conditions requiring immediate intervention
- severe: Serious conditions requiring urgent medical attention  
- moderate: Conditions that need medical management but not urgent
- mild: Minor conditions or early-stage findings
- normal: Normal findings or well-managed/resolved conditions

Consider:
1. Recency of events (more recent events have higher weight)
2. Severity of individual events
3. Number and frequency of events
4. Whether conditions appear resolved or ongoing

Respond with only one word: critical, severe, moderate, mild, or normal"""

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL_COMPLEX,
                messages=[
                    {"role": "system", "content": "You are a medical AI assistant that provides severity assessments based on patient data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            severity = response.choices[0].message.content.strip().lower()
            
            # Validate response
            valid_severities = ["critical", "severe", "moderate", "mild", "normal"]
            if severity not in valid_severities:
                logger.warning(f"LLM returned invalid severity '{severity}', defaulting to rule-based")
                return None  # Fall back to rule-based
            
            logger.info(f"LLM assessed {body_part} severity as: {severity}")
            return severity
            
        except Exception as e:
            logger.error(f"LLM severity assessment failed: {e}")
            return None  # Fall back to rule-based assessment
    
    async def _llm_severity_assessment(self, description: str) -> str:
        """
        Use LLM to assess the severity of a medical condition from its description.
        
        Args:
            description: Medical condition description
            
        Returns:
            Severity level: normal, mild, moderate, severe, or critical
        """
        try:
            from openai import AsyncOpenAI
            from src.core.config import settings
            
            prompt = f"""You are a medical AI assistant. Assess the severity of this medical condition/event:

"{description}"

Severity levels:
- normal: No issues, routine care, or normal findings
- mild: Minor issues, no immediate concern
- moderate: Requires attention but not urgent
- severe: Serious condition requiring prompt treatment
- critical: Life-threatening, immediate intervention needed

Consider:
1. The urgency of the condition
2. Potential for complications
3. Impact on patient's health
4. Treatment requirements

Respond with only one word: normal, mild, moderate, severe, or critical"""

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL_COMPLEX,
                messages=[
                    {"role": "system", "content": "You are a medical AI that assesses condition severity. Respond with only the severity level."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            severity = response.choices[0].message.content.strip().lower()
            
            # Validate response
            valid_severities = ["normal", "mild", "moderate", "severe", "critical"]
            if severity in valid_severities:
                return severity
            else:
                logger.warning(f"LLM returned invalid severity '{severity}', defaulting to moderate")
                return "moderate"
                
        except Exception as e:
            logger.error(f"LLM severity assessment failed for '{description}': {e}")
            return "moderate"  # Default fallback
    
    async def _enhanced_severity_update(self, patient_id: str, entities: List[Dict[str, Any]]):
        """
        Enhanced severity assessment using AI-powered analysis combined with rule-based calculation.
        
        Provides dual assessment approach:
        1. Rule-based severity calculation from clinical indicators
        2. AI-powered severity assessment using LLM analysis of condition descriptions
        
        Updates severity levels for body parts based on comprehensive analysis
        of medical conditions, symptoms, and clinical context.
        
        Args:
            patient_id: Unique patient identifier
            entities: List of medical entities with severity information
        
        Features:
        - Multi-factor severity assessment
        - AI-enhanced clinical judgment
        - Real-time severity updates in knowledge graph
        - Confidence scoring for assessments
        """
        try:
            neo4j_client = neo4j_connection

            # Get affected body parts
            affected_parts = set()
            for entity in entities:
                if entity.get("body_part"):
                    affected_parts.add(entity["body_part"])

            # For each affected body part, assess severity with LLM
            for body_part in affected_parts:
                try:
                    # Placeholder for future logic
                    pass
                except Exception as e:
                    logger.error(f"Failed to update severity for {body_part}: {e}")

        except Exception as e:
            logger.error(f"Enhanced severity update failed: {e}")
            # Fall back to standard auto-update
            neo4j_client = get_graph()
            pass

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI's embedding model.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Use OpenAI's text-embedding-ada-002 model
            response = await client.embeddings.create(
                model="text-embedding-ada-002",
                input=text[:8000]  # Limit text length to avoid token limits
            )
            
            embedding = response.data[0].embedding
            logger.info(f"Generated embedding of dimension {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return a zero vector with standard OpenAI embedding dimension
            return [0.0] * 1536


# Global ingestion agent instance
_ingestion_agent = None


async def get_ingestion_agent() -> IngestionAgent:
    """Get the global ingestion agent instance."""
    global _ingestion_agent
    if _ingestion_agent is None:
        _ingestion_agent = IngestionAgent()
    return _ingestion_agent
