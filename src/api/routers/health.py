"""
Health status endpoints
Handles body parts health status, severity levels, and health summaries
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, List, Optional
from datetime import datetime
import logging

from src.api.dependencies import get_current_user, get_db_clients, require_patient_access
from src.auth.dependencies import get_authenticated_patient_id, AuthenticatedPatientId
from src.models.health import BodyPartHealth, SeverityLevel, HealthSummary, VisualizationData
from src.core.config import settings
from src.core.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/summary")
@limiter.limit("1000/hour")
async def get_health_summary(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get comprehensive health summary for the patient
    """
    try:
        # Handle different user object types
        if hasattr(current_user, 'get'):
            # Dictionary-like user object
            patient_id = current_user.get("patient_id") or current_user.get("user_id") or current_user.get("sub")
        else:
            # User object with attributes
            patient_id = getattr(current_user, 'patient_id', None) or getattr(current_user, 'id', None) or getattr(current_user, 'email', None)
        
        if not patient_id:
            raise HTTPException(status_code=400, detail="Unable to identify patient")
        
        # Initialize summary data
        health_summary = {
            "patient_id": patient_id,
            "summary_date": datetime.utcnow().isoformat(),
            "total_documents": 0,
            "processed_documents": 0,
            "conditions": [],
            "medications": [],
            "symptoms": [],
            "affected_body_parts": [],
            "last_updated": None
        }
        
        if db_clients.get("mongodb") is not None:
            mongodb = db_clients["mongodb"]
            
            # Get document counts
            total_docs = await mongodb.documents.count_documents({"patient_id": patient_id})
            processed_docs = await mongodb.documents.count_documents({
                "patient_id": patient_id, 
                "status": "completed"
            })
            
            health_summary["total_documents"] = total_docs
            health_summary["processed_documents"] = processed_docs
            
            # Get all medical entities from documents
            documents = await mongodb.documents.find({
                "patient_id": patient_id,
                "status": "completed"
            }).to_list(length=50)
            
            all_conditions = set()
            all_medications = set()
            all_symptoms = set()
            all_body_parts = set()
            latest_date = None
            
            for doc in documents:
                if doc.get("processed_at"):
                    doc_date = doc["processed_at"]
                    if latest_date is None or doc_date > latest_date:
                        latest_date = doc_date
                
                summary = doc.get("extracted_data_summary", {})
                if summary.get("conditions"):
                    all_conditions.update(summary["conditions"])
                if summary.get("medications"):
                    all_medications.update(summary["medications"])
                if summary.get("symptoms"):
                    all_symptoms.update(summary["symptoms"])
                if summary.get("body_parts"):
                    all_body_parts.update(summary["body_parts"])
            
            health_summary.update({
                "conditions": list(all_conditions),
                "medications": list(all_medications),
                "symptoms": list(all_symptoms),
                "affected_body_parts": list(all_body_parts),
                "last_updated": latest_date.isoformat() if latest_date else None
            })
        
        # Add Neo4j data if available
        if db_clients.get("neo4j") is not None:
            try:
                neo4j = db_clients["neo4j"]
                entity_result = neo4j.execute_query("""
                    MATCH (p:Patient {patient_id: $patient_id})-[:HAS_DOCUMENT]->(d:Document)
                    -[:EXTRACTED]->(e:Entity)
                    RETURN e.type as entity_type, collect(DISTINCT e.text) as entities
                """, {"patient_id": patient_id})
                
                neo4j_data = {}
                for record in entity_result:
                    neo4j_data[record["entity_type"]] = record["entities"]
                
                # Merge Neo4j data with MongoDB data
                if neo4j_data.get("conditions"):
                    health_summary["conditions"] = list(set(health_summary["conditions"] + neo4j_data["conditions"]))
                if neo4j_data.get("medications"):
                    health_summary["medications"] = list(set(health_summary["medications"] + neo4j_data["medications"]))
                if neo4j_data.get("symptoms"):
                    health_summary["symptoms"] = list(set(health_summary["symptoms"] + neo4j_data["symptoms"]))
                if neo4j_data.get("body_parts"):
                    health_summary["affected_body_parts"] = list(set(health_summary["affected_body_parts"] + neo4j_data["body_parts"]))
                    
            except Exception as e:
                logger.warning(f"Neo4j query failed: {e}")
        
        return health_summary
        
    except Exception as e:
        logger.error(f"Health summary error: {e}")
        raise HTTPException(status_code=500, detail="Health summary service temporarily unavailable")


@router.get("/body-parts")
@limiter.limit("1000/hour")
async def get_body_parts_analysis(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get analysis of affected body parts
    """
    try:
        # Handle different user object types
        if hasattr(current_user, 'get'):
            # Dictionary-like user object
            patient_id = current_user.get("patient_id") or current_user.get("user_id") or current_user.get("sub")
        else:
            # User object with attributes
            patient_id = getattr(current_user, 'patient_id', None) or getattr(current_user, 'id', None) or getattr(current_user, 'email', None)
        
        if not patient_id:
            raise HTTPException(status_code=400, detail="Unable to identify patient")
        
        body_parts_analysis = {
            "patient_id": patient_id,
            "analysis_date": datetime.utcnow().isoformat(),
            "affected_body_parts": {},
            "severity_summary": {
                "high": 0,
                "moderate": 0,
                "mild": 0,
                "unknown": 0
            }
        }
        
        if db_clients.get("mongodb") is not None:
            mongodb = db_clients["mongodb"]
            
            documents = await mongodb.documents.find({
                "patient_id": patient_id,
                "status": "completed"
            }).to_list(length=50)
            
            body_part_conditions = {}
            
            for doc in documents:
                summary = doc.get("extracted_data_summary", {})
                body_parts = summary.get("body_parts", [])
                conditions = summary.get("conditions", [])
                symptoms = summary.get("symptoms", [])
                
                for body_part in body_parts:
                    if body_part not in body_part_conditions:
                        body_part_conditions[body_part] = {
                            "conditions": set(),
                            "symptoms": set(),
                            "severity": "unknown"
                        }
                    
                    body_part_conditions[body_part]["conditions"].update(conditions)
                    body_part_conditions[body_part]["symptoms"].update(symptoms)
                    
                    # Simple severity assessment
                    if any(term in " ".join(conditions + symptoms).lower() for term in ["severe", "acute", "critical"]):
                        body_part_conditions[body_part]["severity"] = "high"
                    elif any(term in " ".join(conditions + symptoms).lower() for term in ["moderate", "chronic"]):
                        body_part_conditions[body_part]["severity"] = "moderate"
                    elif conditions or symptoms:
                        body_part_conditions[body_part]["severity"] = "mild"
            
            # Convert to final format
            for body_part, data in body_part_conditions.items():
                body_parts_analysis["affected_body_parts"][body_part] = {
                    "conditions": list(data["conditions"]),
                    "symptoms": list(data["symptoms"]),
                    "severity": data["severity"],
                    "condition_count": len(data["conditions"]),
                    "symptom_count": len(data["symptoms"])
                }
                
                # Update severity summary
                severity = data["severity"]
                body_parts_analysis["severity_summary"][severity] += 1
        
        return body_parts_analysis
        
    except Exception as e:
        logger.error(f"Body parts analysis error: {e}")
        raise HTTPException(status_code=500, detail="Body parts analysis service temporarily unavailable")


@router.get("/3d-visualization")
@limiter.limit("1000/hour")
async def get_3d_visualization_data(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get data for 3D body visualization
    """
    try:
        # Handle different user object types
        if hasattr(current_user, 'get'):
            # Dictionary-like user object
            patient_id = current_user.get("patient_id") or current_user.get("user_id") or current_user.get("sub")
        else:
            # User object with attributes
            patient_id = getattr(current_user, 'patient_id', None) or getattr(current_user, 'id', None) or getattr(current_user, 'email', None)
        
        if not patient_id:
            raise HTTPException(status_code=400, detail="Unable to identify patient")
        
        visualization_data = {
            "patient_id": patient_id,
            "generated_at": datetime.utcnow().isoformat(),
            "body_regions": {},
            "severity_mapping": {
                "high": {"color": "#FF4444", "opacity": 0.8},
                "moderate": {"color": "#FF8844", "opacity": 0.6},
                "mild": {"color": "#FFAA44", "opacity": 0.4},
                "unknown": {"color": "#CCCCCC", "opacity": 0.2}
            },
            "affected_systems": []
        }
        
        if db_clients.get("mongodb") is not None:
            mongodb = db_clients["mongodb"]
            
            documents = await mongodb.documents.find({
                "patient_id": patient_id,
                "status": "completed"
            }).to_list(length=50)
            
            # Body region mapping
            body_region_map = {
                "heart": "cardiovascular",
                "lungs": "respiratory", 
                "brain": "neurological",
                "liver": "digestive",
                "kidneys": "urinary",
                "stomach": "digestive",
                "intestines": "digestive",
                "joints": "musculoskeletal",
                "muscles": "musculoskeletal",
                "bones": "musculoskeletal",
                "skin": "integumentary",
                "eyes": "sensory",
                "ears": "sensory"
            }
            
            system_conditions = {}
            
            for doc in documents:
                summary = doc.get("extracted_data_summary", {})
                body_parts = summary.get("body_parts", [])
                conditions = summary.get("conditions", [])
                
                for body_part in body_parts:
                    # Map to body system
                    system = body_region_map.get(body_part.lower(), "other")
                    
                    if system not in system_conditions:
                        system_conditions[system] = {
                            "body_parts": set(),
                            "conditions": set(),
                            "severity": "unknown"
                        }
                    
                    system_conditions[system]["body_parts"].add(body_part)
                    system_conditions[system]["conditions"].update(conditions)
                    
                    # Assess severity
                    if any(term in " ".join(conditions).lower() for term in ["severe", "acute", "critical"]):
                        system_conditions[system]["severity"] = "high"
                    elif any(term in " ".join(conditions).lower() for term in ["moderate", "chronic"]):
                        if system_conditions[system]["severity"] != "high":
                            system_conditions[system]["severity"] = "moderate"
                    elif conditions:
                        if system_conditions[system]["severity"] not in ["high", "moderate"]:
                            system_conditions[system]["severity"] = "mild"
            
            # Convert to visualization format
            for system, data in system_conditions.items():
                visualization_data["body_regions"][system] = {
                    "affected_parts": list(data["body_parts"]),
                    "conditions": list(data["conditions"]),
                    "severity": data["severity"],
                    "color": visualization_data["severity_mapping"][data["severity"]]["color"],
                    "opacity": visualization_data["severity_mapping"][data["severity"]]["opacity"]
                }
                
                if data["conditions"]:
                    visualization_data["affected_systems"].append(system)
        
        return visualization_data
        
    except Exception as e:
        logger.error(f"3D visualization error: {e}")
        raise HTTPException(status_code=500, detail="3D visualization service temporarily unavailable")


@router.get("/body-part/{body_part}")
@limiter.limit("1000/hour")
async def get_body_part_details(
    request: Request,
    body_part: str,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get detailed information about a specific body part
    """
    try:
        patient_id = current_user.get("patient_id") or current_user.get("user_id")
        
        body_part_details = {
            "patient_id": patient_id,
            "body_part": body_part,
            "analysis_date": datetime.utcnow().isoformat(),
            "conditions": [],
            "symptoms": [],
            "medications": [],
            "severity": "unknown",
            "affected_documents": [],
            "recommendations": []
        }
        
        if db_clients.get("mongodb"):
            mongodb = db_clients["mongodb"]
            
            documents = await mongodb.documents.find({
                "patient_id": patient_id,
                "status": "completed"
            }).to_list(length=50)
            
            conditions_set = set()
            symptoms_set = set()
            medications_set = set()
            affected_docs = []
            
            for doc in documents:
                summary = doc.get("extracted_data_summary", {})
                body_parts = summary.get("body_parts", [])
                
                # Check if this body part is mentioned
                if any(bp.lower() == body_part.lower() for bp in body_parts):
                    affected_docs.append({
                        "document_id": doc["document_id"],
                        "filename": doc.get("filename", "Unknown"),
                        "processed_at": doc.get("processed_at")
                    })
                    
                    conditions_set.update(summary.get("conditions", []))
                    symptoms_set.update(summary.get("symptoms", []))
                    medications_set.update(summary.get("medications", []))
            
            body_part_details.update({
                "conditions": list(conditions_set),
                "symptoms": list(symptoms_set),
                "medications": list(medications_set),
                "affected_documents": affected_docs
            })
            
            # Assess severity
            all_medical_text = " ".join(list(conditions_set) + list(symptoms_set)).lower()
            if any(term in all_medical_text for term in ["severe", "acute", "critical"]):
                body_part_details["severity"] = "high"
            elif any(term in all_medical_text for term in ["moderate", "chronic"]):
                body_part_details["severity"] = "moderate"
            elif conditions_set or symptoms_set:
                body_part_details["severity"] = "mild"
            
            # Generate basic recommendations
            if conditions_set:
                body_part_details["recommendations"].append(f"Regular monitoring of {body_part} health is recommended")
                body_part_details["recommendations"].append("Follow up with your healthcare provider for ongoing management")
            if symptoms_set:
                body_part_details["recommendations"].append("Track symptoms and report changes to your healthcare team")
        
        return body_part_details
        
    except Exception as e:
        logger.error(f"Body part details error: {e}")
        raise HTTPException(status_code=500, detail="Body part analysis service temporarily unavailable")


@router.get("/body-parts", response_model=Dict[str, BodyPartHealth])
@limiter.limit("1000/hour")
async def get_all_body_parts_health(
    request: Request,
    patient_id: AuthenticatedPatientId,
    include_empty: bool = True,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients),
    _: str = Depends(require_patient_access)
):
    """
    Get health status for all body parts, including severity levels
    for the digital twin visualization.
    """
    try:
        if not db_clients.get("neo4j"):
            raise HTTPException(status_code=503, detail="Neo4j not available")
        body_parts_health = {}
        
        # Get body part health data from Neo4j
        neo4j = db_clients["neo4j"]
        
        # Query for body parts with health data
        health_result = await neo4j.execute_query("""
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_BODY_PART]->(bp:BodyPart)
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(e:Entity)
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(c:Condition)
            OPTIONAL MATCH (bp)<-[:TARGETS]-(t:Treatment)
            
            WITH bp, 
                 collect(DISTINCT e.text) as entities,
                 collect(DISTINCT c.name) as conditions,
                 collect(DISTINCT t.name) as treatments,
                 avg(e.severity) as avg_severity,
                 max(e.date) as last_updated,
                 count(DISTINCT e) as data_points
            
            RETURN bp.name as body_part,
                   avg_severity,
                   last_updated,
                   data_points,
                   conditions,
                   treatments
            ORDER BY bp.name
        """, {"patient_id": patient_id})
        
        # Process results
        for record in health_result:
            body_part = record["body_part"]
            severity = record["avg_severity"] or 0
            
            # Determine severity level
            severity_level = _get_severity_level(severity)
            
            # Parse last updated
            last_updated = None
            if record["last_updated"]:
                try:
                    if isinstance(record["last_updated"], str):
                        last_updated = datetime.fromisoformat(record["last_updated"])
                    else:
                        last_updated = record["last_updated"]
                except:
                    pass
            
            body_parts_health[body_part] = BodyPartHealth(
                body_part=body_part,
                severity=severity if severity > 0 else None,
                severity_level=severity_level,
                last_updated=last_updated,
                data_points=record["data_points"] or 0,
                conditions=record["conditions"] or [],
                treatments=record["treatments"] or []
            )
        
        # Add empty body parts if requested
        if include_empty:
            for body_part in settings.BODY_PARTS:
                if body_part not in body_parts_health:
                    body_parts_health[body_part] = BodyPartHealth(
                        body_part=body_part,
                        severity=None,
                        severity_level=SeverityLevel.UNKNOWN,
                        last_updated=None,
                        data_points=0,
                        conditions=[],
                        treatments=[]
                    )
        
        return body_parts_health
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_all_body_parts_health: {e}")
        raise HTTPException(status_code=503, detail="Database error")

@router.get("/summary", response_model=HealthSummary)
@limiter.limit("1000/hour")
async def get_patient_health_summary(
    request: Request,
    patient_id: str = Depends(get_authenticated_patient_id),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get summary data for the digital twin dashboard.
    """
    try:
        if not db_clients.get("neo4j"):
            raise HTTPException(status_code=503, detail="Neo4j not available")
        # Get summary statistics from various sources
        mongodb = db_clients["mongodb"]
        neo4j = db_clients["neo4j"]
        
        # Get document count
        recent_documents = await mongodb.documents.count_documents({
            "patient_id": patient_id,
            "status": "completed"
        })
        
        # Get health statistics from Neo4j
        stats_result = await neo4j.execute_query("""
            MATCH (p:Patient {patient_id: $patient_id})
            OPTIONAL MATCH (p)-[:HAS_CONDITION]->(c:Condition {status: 'active'})
            OPTIONAL MATCH (p)-[:HAS_MEDICATION]->(m:Medication {status: 'active'})
            OPTIONAL MATCH (p)-[:HAS_BODY_PART]->(bp:BodyPart)<-[:AFFECTS]-(e:Entity)
            OPTIONAL MATCH (p)-[:HAS_EVENT]->(ev:Event)
            
            WITH p,
                 count(DISTINCT c) as active_conditions,
                 count(DISTINCT m) as medications_count,
                 count(DISTINCT bp) as body_parts_affected,
                 count(DISTINCT ev) as timeline_events_count,
                 avg(e.severity) as overall_health_score
            
            RETURN active_conditions,
                   medications_count,
                   body_parts_affected,
                   timeline_events_count,
                   COALESCE(overall_health_score, 8.0) as overall_health_score
        """, {"patient_id": patient_id})
        
        # Default values
        stats = {
            "active_conditions": 0,
            "medications_count": 0,
            "body_parts_affected": 0,
            "timeline_events_count": 0,
            "overall_health_score": 8.0
        }
        
        if stats_result:
            record = stats_result[0]
            stats.update({
                "active_conditions": record["active_conditions"] or 0,
                "medications_count": record["medications_count"] or 0,
                "body_parts_affected": record["body_parts_affected"] or 0,
                "timeline_events_count": record["timeline_events_count"] or 0,
                "overall_health_score": 10 - (record["overall_health_score"] or 2.0)  # Invert severity to health score
            })
        
        # Get critical alerts
        critical_alerts = []
        alerts_result = await neo4j.execute_query("""
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_CONDITION]->(c:Condition)
            WHERE c.severity >= 8 AND c.status = 'active'
            RETURN c.name as condition, c.severity as severity
            ORDER BY c.severity DESC
            LIMIT 5
        """, {"patient_id": patient_id})
        
        for record in alerts_result:
            critical_alerts.append(f"Critical: {record['condition']} (Severity: {record['severity']}/10)")
        
        return HealthSummary(
            patient_id=patient_id,
            last_updated=datetime.utcnow(),
            overall_health_score=min(10, max(0, stats["overall_health_score"])),
            active_conditions=stats["active_conditions"],
            upcoming_appointments=0,  # Would come from appointment system
            medications_count=stats["medications_count"],
            recent_documents=recent_documents,
            critical_alerts=critical_alerts,
            body_parts_affected=stats["body_parts_affected"],
            timeline_events_count=stats["timeline_events_count"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get health summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/3d-visualization")
@limiter.limit("1000/hour")
async def get_3d_visualization_data(
    request: Request,
    patient_id: str = Depends(get_authenticated_patient_id),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get body part health data formatted for 3D visualization.
    Returns coordinates and severity for the digital twin model.
    """
    try:
        if not db_clients.get("neo4j"):
            raise HTTPException(status_code=503, detail="Neo4j not available")
        # Get body part health data
        neo4j = db_clients["neo4j"]
        
        health_result = await neo4j.execute_query("""
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_BODY_PART]->(bp:BodyPart)
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(e:Entity)
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(c:Condition {status: 'active'})
            
            WITH bp,
                 avg(e.severity) as avg_severity,
                 collect(DISTINCT c.name) as conditions,
                 max(e.date) as last_updated
            
            WHERE avg_severity IS NOT NULL OR size(conditions) > 0
            
            RETURN bp.name as body_part,
                   COALESCE(avg_severity, 0) as severity,
                   conditions,
                   last_updated
        """, {"patient_id": patient_id})
        
        # Map body parts to 3D coordinates and colors
        visualization_data = {}
        
        for record in health_result:
            body_part = record["body_part"]
            severity = record["severity"]
            conditions = record["conditions"] or []
            
            # Get 3D position for body part
            position = _get_body_part_position(body_part)
            
            # Get color based on severity
            color = _get_severity_color(severity)
            
            # Parse last updated
            last_updated = None
            if record["last_updated"]:
                try:
                    if isinstance(record["last_updated"], str):
                        last_updated = datetime.fromisoformat(record["last_updated"])
                    else:
                        last_updated = record["last_updated"]
                except:
                    pass
            
            visualization_data[body_part] = VisualizationData(
                position=position,
                severity=severity,
                color=color,
                label=body_part.replace("_", " ").title(),
                conditions=conditions,
                last_updated=last_updated
            )
        
        return visualization_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get 3D visualization data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/body-part/{body_part}")
@limiter.limit("1000/hour")
async def get_body_part_details(
    request: Request,
    body_part: str,
    patient_id: str = Depends(get_authenticated_patient_id),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get detailed information for a specific body part
    """
    try:
        if not db_clients.get("neo4j"):
            raise HTTPException(status_code=503, detail="Neo4j not available")
        if body_part not in settings.BODY_PARTS:
            raise HTTPException(status_code=400, detail="Invalid body part")
        
        neo4j = db_clients["neo4j"]
        
        # Get detailed body part information
        detail_result = await neo4j.execute_query("""
            MATCH (p:Patient {patient_id: $patient_id})-[:HAS_BODY_PART]->(bp:BodyPart {name: $body_part})
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(e:Entity)
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(c:Condition)
            OPTIONAL MATCH (bp)<-[:TARGETS]-(t:Treatment)
            OPTIONAL MATCH (bp)<-[:AFFECTS]-(ev:Event)
            
            RETURN bp,
                   collect(DISTINCT {
                       type: e.type,
                       text: e.text,
                       severity: e.severity,
                       date: e.date,
                       confidence: e.confidence
                   }) as entities,
                   collect(DISTINCT {
                       name: c.name,
                       severity: c.severity,
                       status: c.status,
                       diagnosed_date: c.diagnosed_date
                   }) as conditions,
                   collect(DISTINCT {
                       name: t.name,
                       type: t.type,
                       start_date: t.start_date,
                       status: t.status
                   }) as treatments,
                   collect(DISTINCT {
                       date: ev.date,
                       type: ev.event_type,
                       description: ev.description
                   }) as events
        """, {"patient_id": patient_id, "body_part": body_part})
        
        if not detail_result:
            return {
                "body_part": body_part,
                "severity": 0,
                "severity_level": SeverityLevel.UNKNOWN,
                "entities": [],
                "conditions": [],
                "treatments": [],
                "events": []
            }
        
        record = detail_result[0]
        
        # Calculate overall severity
        entities = [e for e in record["entities"] if e["severity"] is not None]
        avg_severity = sum(e["severity"] for e in entities) / len(entities) if entities else 0
        
        return {
            "body_part": body_part,
            "severity": avg_severity,
            "severity_level": _get_severity_level(avg_severity),
            "entities": record["entities"],
            "conditions": record["conditions"],
            "treatments": record["treatments"],
            "events": record["events"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get body part details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions

def _get_severity_level(severity: float) -> SeverityLevel:
    """Convert numeric severity to severity level"""
    if severity >= 8:
        return SeverityLevel.CRITICAL
    elif severity >= 6:
        return SeverityLevel.SEVERE
    elif severity >= 4:
        return SeverityLevel.MODERATE
    elif severity >= 2:
        return SeverityLevel.MILD
    elif severity > 0:
        return SeverityLevel.NORMAL
    else:
        return SeverityLevel.UNKNOWN

def _get_severity_color(severity: float) -> str:
    """Get color based on severity level"""
    severity_level = _get_severity_level(severity)
    return settings.SEVERITY_LEVELS[severity_level.value]["color"]

def _get_body_part_position(body_part: str) -> Dict[str, float]:
    """Get 3D position for body part (simplified mapping)"""
    # This would be a comprehensive mapping to 3D coordinates
    # For now, providing basic positioning
    positions = {
        # Head and Neck
        "brain": {"x": 0, "y": 1.7, "z": 0},
        "eyes": {"x": 0, "y": 1.65, "z": 0.1},
        "ears": {"x": 0.15, "y": 1.65, "z": 0},
        "nose": {"x": 0, "y": 1.6, "z": 0.1},
        "throat": {"x": 0, "y": 1.5, "z": 0},
        "neck": {"x": 0, "y": 1.45, "z": 0},
        
        # Torso - Upper
        "shoulder_left": {"x": -0.3, "y": 1.4, "z": 0},
        "shoulder_right": {"x": 0.3, "y": 1.4, "z": 0},
        "chest": {"x": 0, "y": 1.2, "z": 0.1},
        "heart": {"x": -0.05, "y": 1.2, "z": 0},
        "lungs": {"x": 0, "y": 1.2, "z": 0},
        
        # Torso - Mid
        "liver": {"x": 0.1, "y": 0.9, "z": 0},
        "stomach": {"x": -0.05, "y": 0.9, "z": 0},
        "pancreas": {"x": 0, "y": 0.85, "z": -0.05},
        "spleen": {"x": -0.15, "y": 0.9, "z": 0},
        
        # Torso - Lower
        "kidneys": {"x": 0, "y": 0.8, "z": -0.1},
        "bladder": {"x": 0, "y": 0.6, "z": 0},
        "intestines_small": {"x": 0, "y": 0.7, "z": 0},
        "intestines_large": {"x": 0, "y": 0.65, "z": 0},
        
        # Extremities
        "arm_left": {"x": -0.5, "y": 1.0, "z": 0},
        "arm_right": {"x": 0.5, "y": 1.0, "z": 0},
        "leg_left": {"x": -0.15, "y": 0.3, "z": 0},
        "leg_right": {"x": 0.15, "y": 0.3, "z": 0},
        "hand_left": {"x": -0.7, "y": 0.8, "z": 0},
        "hand_right": {"x": 0.7, "y": 0.8, "z": 0},
        "foot_left": {"x": -0.15, "y": 0, "z": 0},
        "foot_right": {"x": 0.15, "y": 0, "z": 0},
    }
    
    return positions.get(body_part, {"x": 0, "y": 1, "z": 0})
