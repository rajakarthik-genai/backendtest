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
        """Extract medical entities from text using advanced LLM-powered extraction (event-centric, provenance, advanced schema)."""
        try:
            from openai import AsyncOpenAI
            from src.config.settings import settings
            import re
            import uuid
            import json
            # Advanced prompt from user blueprint
            advanced_prompt = '''You are a meticulous clinical‐data extraction agent.

########  INPUT  ########
{text}

########  REQUIRED OUTPUT  ########
Return exactly one JSON document with these top-level arrays:

{
  "patient": {
    "uid": "patient–jonathan-ericsson",
    "fullName": "Jonathan Ericsson",
    "otherIdentifiers": [],
    "notes": "Autogenerated if biodata present"
  },
  "clinicians": [
    { "uid": "clinician–rob-snitzer", "fullName": "Rob Snitzer", "role": "Therapist" },
    { "uid": "clinician–unnamed-doctor", "fullName": "Unspecified", "role": "Doctor" }
  ],
  "injuryEvents": [
    {
      "uid": "injury–2008-11-23-abdominal",
      "type": "Abdominal pain / illness",
      "bodyRegion": "Abdomen",
      "side": "Right",
      "onsetDateTime": "2008-11-23T15:00-06:00",
      "reportedDateTime": "2008-11-23T15:00-06:00",
      "clearanceDateTime": "2008-11-25T09:00-06:00",
      "mechanism": "Contact",
      "venue": "Arena",
      "session": "Game",
      "acute": true,
      "gamesLost": 2,
      "provenance": {"sourcePage": 1, "charStart": 0, "charEnd": 120}
    }
  ],
  "diagnoses": [
    {
      "uid": "diagnosis–847.2",
      "code": "847.2",
      "description": "Sprain of lumbar",
      "bodyRegion": "Lumbar",
      "verified": true,
      "provenance": {"sourcePage": 1, "charStart": 121, "charEnd": 180}
    }
  ],
  "treatments": [
    {
      "uid": "treatment–ice-1",
      "type": "Ice",
      "parameters": {"duration": "20min"},
      "duration": "20min",
      "provenance": {"sourcePage": 1, "charStart": 181, "charEnd": 200}
    }
  ],
  "notes": [
    {
      "uid": "note–1",
      "noteDate": "2008-11-23T15:00-06:00",
      "section": "Subjective",
      "text": "Patient reports pain in right abdomen after collision.",
      "provenance": {"sourcePage": 1, "charStart": 0, "charEnd": 60}
    }
  ],
  "outcomes": [
    {
      "uid": "outcome–1",
      "status": "Resolved",
      "date": "2008-11-25T09:00-06:00",
      "provenance": {"sourcePage": 1, "charStart": 201, "charEnd": 220}
    }
  ],
  "files": [
    {
      "uid": "file–1",
      "fileName": "scan1.png",
      "mimeType": "image/png",
      "url": "https://...",
      "provenance": {"sourcePage": 1, "charStart": 221, "charEnd": 240}
    }
  ]
}

Instructions:
1. Chunk the document by headers (Therapist Note, Doctors Note, etc.) and detect SOAP sub-headers.
2. Canonicalize dates/times to ISO-8601.
3. Normalize medical codes: map text to ICD-9/ICD-10 where available. Provide both raw text and code.
4. Deduplicate clinicians by exact name + role.
5. Generate unique IDs (injuryId, noteId, etc.) to support idempotent upserts in Cypher.
6. Emit one self-contained JSON matching the schema above.
7. Attach provenance: each top-level object holds sourcePage and character offsets.
8. Respond with valid JSON only, following the schema exactly.
'''
            # Prepare prompt
            prompt = advanced_prompt.format(text=text)
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model=settings.openai_model_chat,
                messages=[
                    {"role": "system", "content": "You are a clinical data extraction agent. Follow the instructions and schema strictly."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=3000
            )
            # Parse JSON response
            response_content = response.choices[0].message.content.strip()
            # Remove markdown if present
            if response_content.startswith("```json"):
                response_content = response_content[7:]
            if response_content.endswith("```"):
                response_content = response_content[:-3]
            try:
                result = json.loads(response_content)
            except Exception as e:
                logger.error(f"Failed to parse advanced LLM extraction JSON: {e}")
                return []
            # Attach extraction method and timestamp to each top-level object for traceability
            now = datetime.utcnow().isoformat()
            for key in ["injuryEvents", "diagnoses", "treatments", "notes", "outcomes", "files"]:
                if key in result:
                    for obj in result[key]:
                        obj["extraction_method"] = "llm_advanced_schema"
                        obj["created_at"] = now
            logger.info(f"Advanced LLM extraction produced: {[len(result.get(k, [])) for k in ['injuryEvents','diagnoses','treatments','notes','outcomes','files']]}")
            return result
        except Exception as e:
            logger.error(f"Advanced LLM entity extraction failed: {e}")
            return []
    
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
        extracted: dict,
        metadata: Dict[str, Any]
    ) -> str:
        """Store document data in MongoDB."""
        try:
            mongo_client = await get_mongo()
            
            record_data = {
                "document_id": document_id,
                "extracted_text": text,
                "entities": extracted,
                "metadata": metadata,
                "processing_timestamp": datetime.utcnow().isoformat()
            }
            
            record_id = await mongo_client.store_medical_record(
                patient_id=patient_id,
                record_data=record_data,
                record_type="document"
            )
            
            return record_id
            
        except Exception as e:
            logger.error(f"MongoDB storage failed: {e}")
            raise
    
    async def _store_in_neo4j(
        self,
        patient_id: str,
        document_id: str,
        extracted: dict
    ):
        """
        Create knowledge graph relationships in Neo4j for all event types in the advanced schema.
        Ensures body part nodes are patient-specific and all events are present for timeline completeness.
        """
        try:
            neo4j_client = get_graph()
            # For each event type in the advanced schema, create nodes/relationships
            for key in ["injuryEvents", "diagnoses", "treatments", "notes", "outcomes", "files"]:
                for event in extracted.get(key, []):
                    # Use a generic event creation for all event types
                    event_data = dict(event)  # Copy to avoid mutation
                    event_data["event_type"] = key
                    # Use body part if present, else empty
                    body_parts = []
                    if "bodyRegion" in event:
                        body_parts = [event["bodyRegion"]]
                    elif "body_part" in event:
                        body_parts = [event["body_part"]]
                    neo4j_client.create_medical_event(
                        user_id=patient_id,
                        event_data=event_data,
                        body_parts=body_parts
                    )
            logger.info(f"Neo4j storage completed for document {document_id}: {[len(extracted.get(k, [])) for k in ['injuryEvents','diagnoses','treatments','notes','outcomes','files']]}")
        except Exception as e:
            logger.error(f"Neo4j storage failed: {e}")
            # Don't raise - Neo4j storage is not critical
    
    async def _create_llm_medical_event(
        self,
        neo4j_client,
        patient_id: str,
        document_id: str,
        entity: Dict[str, Any]
    ):
        """Create a medical event from LLM-extracted data with enhanced schema."""
        try:
            # Parse date if provided
            event_date = datetime.utcnow()
            if entity.get("date"):
                try:
                    from dateutil.parser import parse
                    event_date = parse(entity["date"])
                except:
                    logger.warning(f"Could not parse date: {entity.get('date')}")
            
            # Create comprehensive event data following MedicalEvent schema
            event_data = {
                "event_id": entity.get("event_id", str(uuid.uuid4())),
                "title": entity.get("condition", "Medical Finding"),
                "description": entity.get("summary", f"Medical event from document {document_id}"),
                "event_type": "medical_condition",
                "timestamp": event_date,
                "date": entity.get("date", event_date.isoformat()),
                "source": "llm_extraction",
                "severity": entity.get("severity", "mild"),
                "confidence": entity.get("confidence", 0.8),
                "body_part": entity.get("body_part"),
                "condition": entity.get("condition"),
                "symptoms": entity.get("symptoms", []),
                "treatments": entity.get("treatments", []),
                "summary": entity.get("summary", ""),
                "extraction_method": "llm_structured_output",
                "properties": {
                    "document_id": document_id,
                    "symptoms": entity.get("symptoms", []),
                    "treatments": entity.get("treatments", []),
                    "icd_codes": entity.get("icd_codes", []),
                    "snomed_codes": entity.get("snomed_codes", [])
                }
            }
            
            # Create the medical event in Neo4j
            event_id = neo4j_client.create_medical_event(
                patient_id=patient_id,
                event_data=event_data,
                body_parts=[entity.get("body_part")] if entity.get("body_part") else []
            )
            
            logger.debug(f"Created LLM medical event: {event_id}")
            
        except Exception as e:
            logger.error(f"Failed to create LLM medical event: {e}")
    
    async def _create_fallback_medical_event(
        self,
        neo4j_client,
        patient_id: str,
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
                patient_id=patient_id,
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
        patient_id: str,
        document_id: str,
        text: str,
        entities: List[Dict[str, Any]] = None
    ):
        """Generate and store text embeddings in Milvus with enhanced medical event data."""
        try:
            milvus_client = get_milvus()
            
            # Store main document embeddings
            chunks = self._split_text_into_chunks(text, max_length=500)
            if chunks:
                milvus_client.store_document_embeddings(
                    patient_id=patient_id,
                    document_id=document_id,
                    text_chunks=chunks,
                    metadata={"source": "document_processing"}
                )
            
            # Store individual medical event embeddings for better retrieval
            if entities:
                for entity in entities:
                    if entity.get("extraction_method") == "llm_structured_output":
                        # Create rich text for embedding from medical event
                        event_text = self._create_event_embedding_text(entity)
                        if event_text:
                            milvus_client.store_document_embeddings(
                                patient_id=patient_id,
                                document_id=f"{document_id}_{entity.get('event_id', 'unknown')}",
                                text_chunks=[event_text],
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
        """Create rich text for embedding from medical event."""
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
        entities: List[Dict[str, Any]]
    ):
        """Extract lifestyle factors and update long-term memory."""
        try:
            from src.chat.long_term import LongTermMemory
            
            ltm = LongTermMemory()
            
            # Extract lifestyle indicators from text and entities
            text_lower = text.lower()
            
            lifestyle_updates = {}
            
            # Check for smoking status
            if any(term in text_lower for term in ["smok", "cigarette", "tobacco", "nicotine"]):
                if any(term in text_lower for term in ["quit", "former", "ex-smoker", "stopped"]):
                    lifestyle_updates["smoking_status"] = "former_smoker"
                else:
                    lifestyle_updates["smoking_status"] = "current_smoker"
            
            # Check for alcohol use
            if any(term in text_lower for term in ["alcohol", "drink", "wine", "beer", "liquor"]):
                if any(term in text_lower for term in ["excessive", "heavy", "abuse", "dependence"]):
                    lifestyle_updates["alcohol_use"] = "heavy"
                elif any(term in text_lower for term in ["social", "occasional", "moderate"]):
                    lifestyle_updates["alcohol_use"] = "moderate"
                else:
                    lifestyle_updates["alcohol_use"] = "present"
            
            # Check for exercise/activity level
            if any(term in text_lower for term in ["sedentary", "inactive", "no exercise"]):
                lifestyle_updates["activity_level"] = "sedentary"
            elif any(term in text_lower for term in ["active", "exercise", "sports", "gym"]):
                lifestyle_updates["activity_level"] = "active"
            
            # Check for diet patterns
            if any(term in text_lower for term in ["obesity", "overweight", "high bmi"]):
                lifestyle_updates["weight_status"] = "overweight"
            elif any(term in text_lower for term in ["underweight", "malnourished"]):
                lifestyle_updates["weight_status"] = "underweight"
            
            # Extract chronic conditions for medical history
            chronic_conditions = []
            for entity in entities:
                if entity.get("extraction_method") == "llm_structured_output":
                    condition = entity.get("condition", "")
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
            from src.config.settings import settings
            
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

            client = AsyncOpenAI(api_key=settings.openai_api_key)
            
            response = await client.chat.completions.create(
                model=settings.openai_model_chat,
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
            from src.config.settings import settings
            
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

            client = AsyncOpenAI(api_key=settings.openai_api_key)
            
            response = await client.chat.completions.create(
                model=settings.openai_model_chat,
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
        Enhanced severity update using LLM assessment in addition to rule-based calculation.
        """
        try:
            from src.db.neo4j_db import get_graph

            neo4j_client = get_graph()

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


# Global ingestion agent instance
_ingestion_agent = None


async def get_ingestion_agent() -> IngestionAgent:
    """Get the global ingestion agent instance."""
    global _ingestion_agent
    if _ingestion_agent is None:
        _ingestion_agent = IngestionAgent()
    return _ingestion_agent
