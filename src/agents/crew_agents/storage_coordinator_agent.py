"""
Storage Coordinator Agent for CrewAI pipeline.
Handles storing extracted clinical data in MongoDB with proper patient isolation.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from crewai import Agent, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from bson import ObjectId

from src.utils.logging import logger, log_user_action
from src.db.mongo_db import get_mongo
from src.db.neo4j_db import get_graph


class ClinicalRecord(BaseModel):
    """Model for clinical records in MongoDB."""
    patient_id: str = Field(description="Patient identifier")
    document_id: str = Field(description="Document identifier") 
    document_title: str = Field(description="Document title or type")
    document_date: str = Field(description="Document date")
    clinician: Dict[str, str] = Field(description="Clinician information")
    injuries: List[Dict[str, Any]] = Field(description="Injury information")
    diagnoses: List[Dict[str, Any]] = Field(description="Diagnosis information")
    procedures: List[Dict[str, Any]] = Field(description="Procedure information")
    medications: List[Dict[str, Any]] = Field(description="Medication information")
    clinical_sections: Dict[str, str] = Field(description="SOAP note sections")
    narrative_sections: Dict[str, str] = Field(description="Additional narrative sections")
    timeline: List[Dict[str, Any]] = Field(description="Timeline of events")
    medical_codes: List[Dict[str, str]] = Field(description="Medical codes")
    metadata: Dict[str, Any] = Field(description="Additional metadata")


class MongoStorageTool(BaseTool):
    """Tool for storing clinical data in MongoDB."""
    
    name: str = "mongo_storage"
    description: str = "Store structured clinical data in MongoDB with patient isolation"
    
    def _run(self, clinical_data: Dict[str, Any], document_id: str, user_id: str) -> Dict[str, Any]:
        """Store clinical data in MongoDB."""
        try:
            logger.info(f"Storing clinical data in MongoDB for patient {user_id}")
            
            # Prepare clinical record
            clinical_record = {
                "patient_id": user_id,  # Use the actual user_id for isolation
                "document_id": document_id,
                "document_title": clinical_data.get("document_title", "Unknown"),
                "document_date": clinical_data.get("document_date", "Not Available"),
                "clinician": clinical_data.get("clinician", {}),
                "injuries": clinical_data.get("injuries", []),
                "diagnoses": clinical_data.get("diagnoses", []),
                "procedures": clinical_data.get("procedures", []),
                "medications": clinical_data.get("medications", []),
                "clinical_sections": {
                    "subjective": clinical_data.get("subjective_note_text", ""),
                    "objective": clinical_data.get("objective_note_text", ""),
                    "assessment": clinical_data.get("assessment_note_text", ""),
                    "plan": clinical_data.get("plan_note_text", "")
                },
                "narrative_sections": {
                    "feedback": clinical_data.get("feedback", ""),
                    "recovery_progress": clinical_data.get("recovery_progress", ""),
                    "patient_history": clinical_data.get("patient_history", "")
                },
                "timeline": clinical_data.get("timeline", []),
                "medical_codes": clinical_data.get("medical_codes", []),
                "metadata": {
                    **clinical_data.get("metadata", {}),
                    "stored_at": datetime.utcnow().isoformat(),
                    "storage_version": "1.0",
                    "record_type": "clinical_document"
                }
            }
            
            # Store in MongoDB
            mongo_client = get_mongo()
            result = mongo_client.store_clinical_record(clinical_record)
            
            logger.info(f"Successfully stored clinical record with ID: {result}")
            
            return {
                "success": True,
                "record_id": str(result),
                "patient_id": user_id,
                "document_id": document_id,
                "stored_at": clinical_record["metadata"]["stored_at"]
            }
            
        except Exception as e:
            logger.error(f"MongoDB storage failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


class Neo4jStorageTool(BaseTool):
    """Tool for storing clinical data in Neo4j knowledge graph."""
    
    name: str = "neo4j_storage"
    description: str = "Store clinical data in Neo4j knowledge graph with patient-specific nodes"
    
    def _run(self, clinical_data: Dict[str, Any], document_id: str, user_id: str) -> Dict[str, Any]:
        """Store clinical data in Neo4j."""
        try:
            logger.info(f"Storing clinical data in Neo4j for patient {user_id}")
            
            neo4j_client = get_graph()
            
            # Ensure user graph is initialized
            neo4j_client.ensure_user_initialized(user_id)
            
            stored_events = []
            
            # Process injuries as medical events
            injuries = clinical_data.get("injuries", [])
            for injury in injuries:
                event_data = {
                    "title": injury.get("description", "Unknown injury"),
                    "description": injury.get("description", ""),
                    "event_type": "injury",
                    "severity": injury.get("severity", "moderate"),
                    "body_part": injury.get("body_part", "Unknown"),
                    "date": injury.get("date", datetime.utcnow().isoformat()),
                    "source_document": document_id,
                    "confidence": 0.9,
                    "metadata": injury.get("source", {})
                }
                
                try:
                    event_id = neo4j_client.create_medical_event(user_id, event_data)
                    stored_events.append({"type": "injury", "event_id": event_id})
                except Exception as e:
                    logger.warning(f"Failed to store injury in Neo4j: {e}")
            
            # Process diagnoses as medical events
            diagnoses = clinical_data.get("diagnoses", [])
            for diagnosis in diagnoses:
                event_data = {
                    "title": diagnosis.get("name", "Unknown diagnosis"),
                    "description": f"Diagnosis: {diagnosis.get('name', '')} (Code: {diagnosis.get('code', 'N/A')})",
                    "event_type": "diagnosis",
                    "severity": "moderate",  # Default for diagnoses
                    "body_part": "General",  # Diagnoses may not have specific body parts
                    "date": diagnosis.get("date_diagnosed", datetime.utcnow().isoformat()),
                    "source_document": document_id,
                    "confidence": 0.95,
                    "metadata": {
                        "medical_code": diagnosis.get("code", ""),
                        "status": diagnosis.get("status", "active"),
                        **diagnosis.get("source", {})
                    }
                }
                
                try:
                    event_id = neo4j_client.create_medical_event(user_id, event_data)
                    stored_events.append({"type": "diagnosis", "event_id": event_id})
                except Exception as e:
                    logger.warning(f"Failed to store diagnosis in Neo4j: {e}")
            
            # Process procedures as medical events
            procedures = clinical_data.get("procedures", [])
            for procedure in procedures:
                event_data = {
                    "title": procedure.get("name", "Unknown procedure"),
                    "description": procedure.get("name", ""),
                    "event_type": "procedure",
                    "severity": "mild",  # Default for procedures
                    "body_part": "General",  # Procedures may not have specific body parts
                    "date": procedure.get("date", datetime.utcnow().isoformat()),
                    "source_document": document_id,
                    "confidence": 0.9,
                    "metadata": {
                        "outcome": procedure.get("outcome", ""),
                        **procedure.get("source", {})
                    }
                }
                
                try:
                    event_id = neo4j_client.create_medical_event(user_id, event_data)
                    stored_events.append({"type": "procedure", "event_id": event_id})
                except Exception as e:
                    logger.warning(f"Failed to store procedure in Neo4j: {e}")
            
            # Update body part severities based on events
            try:
                neo4j_client.update_body_part_severities(user_id)
            except Exception as e:
                logger.warning(f"Failed to update body part severities: {e}")
            
            logger.info(f"Successfully stored {len(stored_events)} events in Neo4j")
            
            return {
                "success": True,
                "stored_events": stored_events,
                "total_events": len(stored_events),
                "patient_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Neo4j storage failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "stored_events": []
            }


class LongTermMemoryTool(BaseTool):
    """Tool for extracting and storing lifestyle factors in long-term memory."""
    
    name: str = "long_term_memory"
    description: str = "Extract lifestyle factors and update patient long-term memory"
    
    def _run(self, clinical_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Extract lifestyle factors and update long-term memory."""
        try:
            logger.info(f"Processing long-term memory updates for patient {user_id}")
            
            from src.chat.long_term import LongTermMemory
            
            ltm = LongTermMemory(user_id)
            
            # Extract lifestyle factors from text
            full_text = " ".join([
                clinical_data.get("subjective_note_text", ""),
                clinical_data.get("objective_note_text", ""),
                clinical_data.get("assessment_note_text", ""),
                clinical_data.get("plan_note_text", ""),
                clinical_data.get("patient_history", ""),
                clinical_data.get("feedback", "")
            ]).lower()
            
            lifestyle_updates = {}
            
            # Smoking status
            if any(term in full_text for term in ["smoke", "smoking", "tobacco", "cigarette", "nicotine"]):
                if any(term in full_text for term in ["quit", "stopped", "former", "ex-smoker"]):
                    lifestyle_updates["smoking_status"] = "former_smoker"
                elif any(term in full_text for term in ["current", "active", "still smoking"]):
                    lifestyle_updates["smoking_status"] = "current_smoker"
                else:
                    lifestyle_updates["smoking_status"] = "smoking_history"
            
            # Alcohol consumption
            if any(term in full_text for term in ["alcohol", "drinking", "drinks", "beer", "wine", "liquor"]):
                if any(term in full_text for term in ["excessive", "heavy", "problem", "abuse"]):
                    lifestyle_updates["alcohol_status"] = "excessive_use"
                elif any(term in full_text for term in ["social", "occasional", "moderate"]):
                    lifestyle_updates["alcohol_status"] = "social_drinker"
                else:
                    lifestyle_updates["alcohol_status"] = "alcohol_use"
            
            # Exercise habits
            if any(term in full_text for term in ["exercise", "workout", "gym", "running", "training", "athletic"]):
                if any(term in full_text for term in ["regular", "active", "frequent"]):
                    lifestyle_updates["exercise_level"] = "active"
                elif any(term in full_text for term in ["sedentary", "inactive", "no exercise"]):
                    lifestyle_updates["exercise_level"] = "sedentary"
                else:
                    lifestyle_updates["exercise_level"] = "moderate"
            
            # Chronic conditions
            chronic_conditions = []
            condition_keywords = [
                "diabetes", "hypertension", "heart disease", "arthritis", "asthma",
                "copd", "depression", "anxiety", "obesity", "thyroid"
            ]
            
            for condition in condition_keywords:
                if condition in full_text:
                    chronic_conditions.append(condition)
            
            if chronic_conditions:
                lifestyle_updates["chronic_conditions"] = chronic_conditions
            
            # Update long-term memory
            updates_made = 0
            for key, value in lifestyle_updates.items():
                try:
                    ltm.update_profile(key, value)
                    updates_made += 1
                except Exception as e:
                    logger.warning(f"Failed to update {key} in long-term memory: {e}")
            
            # Add to medical history
            if clinical_data.get("diagnoses"):
                for diagnosis in clinical_data["diagnoses"]:
                    try:
                        ltm.add_medical_history_item(
                            diagnosis.get("name", "Unknown"),
                            clinical_data.get("document_date", datetime.utcnow().isoformat())
                        )
                        updates_made += 1
                    except Exception as e:
                        logger.warning(f"Failed to add medical history item: {e}")
            
            logger.info(f"Made {updates_made} long-term memory updates")
            
            return {
                "success": True,
                "updates_made": updates_made,
                "lifestyle_factors": lifestyle_updates,
                "chronic_conditions": chronic_conditions
            }
            
        except Exception as e:
            logger.error(f"Long-term memory update failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "updates_made": 0
            }


class StorageCoordinatorAgent:
    """CrewAI agent for coordinating data storage across multiple databases."""
    
    def __init__(self):
        self.mongo_tool = MongoStorageTool()
        self.neo4j_tool = Neo4jStorageTool()
        self.ltm_tool = LongTermMemoryTool()
        
        self.agent = Agent(
            role="Clinical Data Storage Coordinator",
            goal="Efficiently and accurately store extracted clinical data across multiple storage systems while maintaining data integrity and patient isolation",
            backstory="""You are a healthcare data management specialist with extensive experience 
            in medical informatics and database administration. You understand the critical importance 
            of maintaining patient data privacy, ensuring data integrity across multiple storage systems,
            and implementing proper data governance in healthcare environments. 
            
            Your expertise includes:
            - HIPAA-compliant data storage and patient data isolation
            - Multi-database coordination (MongoDB, Neo4j, Redis)
            - Medical data normalization and standardization
            - Long-term memory management for patient profiles
            - Knowledge graph construction for medical relationships
            - Data provenance and traceability maintenance""",
            tools=[self.mongo_tool, self.neo4j_tool, self.ltm_tool],
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    def create_storage_task(self, clinical_data: Dict[str, Any], document_id: str, user_id: str) -> Task:
        """Create a task for comprehensive data storage."""
        
        return Task(
            description=f"""
            Coordinate the storage of extracted clinical data across multiple storage systems
            while ensuring data integrity, patient isolation, and proper provenance tracking.
            
            Clinical Data: {json.dumps(clinical_data, indent=2)}
            Document ID: {document_id}
            Patient ID: {user_id}
            
            Your task involves coordinating storage across three systems:
            
            1. **MongoDB Storage** (Structured Data):
               - Store complete clinical record with all extracted information
               - Ensure patient_id isolation (use provided user_id)
               - Include comprehensive metadata for traceability
               - Store SOAP note sections and narrative content
               - Maintain referential integrity with document_id
               - Include storage timestamps and version information
            
            2. **Neo4j Knowledge Graph** (Relationships):
               - Create medical events for injuries, diagnoses, procedures
               - Link events to patient-specific body part nodes
               - Update body part severity scores based on new events
               - Maintain temporal relationships and event sequences
               - Ensure patient graph isolation (user-specific body parts)
               - Store source document references for provenance
            
            3. **Long-Term Memory** (Lifestyle Factors):
               - Extract lifestyle factors (smoking, alcohol, exercise)
               - Identify chronic conditions for persistent tracking
               - Update patient profile with lifestyle information
               - Add significant diagnoses to medical history
               - Maintain continuity across multiple documents
            
            **Critical Requirements**:
            - Use the exact user_id provided for patient isolation
            - Maintain referential integrity across all storage systems
            - Include document_id in all stored records for traceability
            - Handle storage failures gracefully (partial success is acceptable)
            - Log all storage operations for audit purposes
            - Ensure HIPAA compliance in all storage operations
            
            **Success Criteria**:
            - Clinical record successfully stored in MongoDB
            - Medical events created in Neo4j knowledge graph
            - Body part severities updated based on new events
            - Lifestyle factors extracted and stored in long-term memory
            - All storage operations properly logged
            
            Return a comprehensive storage summary including:
            - Storage success status for each system
            - Number of records/events stored in each system
            - Any errors or warnings encountered
            - Storage confirmation IDs where applicable
            """,
            expected_output="Complete storage coordination summary with success status for MongoDB, Neo4j, and long-term memory systems",
            agent=self.agent
        )
    
    def coordinate_storage(self, clinical_data: Dict[str, Any], document_id: str, user_id: str) -> Dict[str, Any]:
        """Coordinate storage across all systems."""
        try:
            logger.info(f"Starting storage coordination for document {document_id}, patient {user_id}")
            
            storage_results = {
                "mongo": {"success": False, "error": None},
                "neo4j": {"success": False, "error": None},
                "ltm": {"success": False, "error": None}
            }
            
            # 1. Store in MongoDB
            try:
                mongo_result = self.mongo_tool._run(clinical_data, document_id, user_id)
                storage_results["mongo"] = mongo_result
                if mongo_result["success"]:
                    logger.info(f"MongoDB storage successful: {mongo_result.get('record_id')}")
            except Exception as e:
                logger.error(f"MongoDB storage failed: {e}")
                storage_results["mongo"]["error"] = str(e)
            
            # 2. Store in Neo4j
            try:
                neo4j_result = self.neo4j_tool._run(clinical_data, document_id, user_id)
                storage_results["neo4j"] = neo4j_result
                if neo4j_result["success"]:
                    logger.info(f"Neo4j storage successful: {neo4j_result.get('total_events')} events")
            except Exception as e:
                logger.error(f"Neo4j storage failed: {e}")
                storage_results["neo4j"]["error"] = str(e)
            
            # 3. Update long-term memory
            try:
                ltm_result = self.ltm_tool._run(clinical_data, user_id)
                storage_results["ltm"] = ltm_result
                if ltm_result["success"]:
                    logger.info(f"Long-term memory update successful: {ltm_result.get('updates_made')} updates")
            except Exception as e:
                logger.error(f"Long-term memory update failed: {e}")
                storage_results["ltm"]["error"] = str(e)
            
            # Calculate overall success
            successful_systems = sum(1 for result in storage_results.values() if result["success"])
            total_systems = len(storage_results)
            
            # Log user action
            log_user_action(
                user_id,
                "clinical_data_stored",
                {
                    "document_id": document_id,
                    "successful_systems": successful_systems,
                    "total_systems": total_systems,
                    "storage_details": storage_results
                }
            )
            
            return {
                "success": successful_systems > 0,  # Partial success is acceptable
                "successful_systems": successful_systems,
                "total_systems": total_systems,
                "storage_results": storage_results,
                "document_id": document_id,
                "patient_id": user_id,
                "stored_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Storage coordination failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "successful_systems": 0,
                "total_systems": 3,
                "storage_results": storage_results
            }
