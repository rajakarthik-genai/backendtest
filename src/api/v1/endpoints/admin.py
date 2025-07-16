"""
Admin endpoints for patient data management and system validation.
Provides endpoints to list, view, and delete patient-specific data across MongoDB, Neo4j, and Milvus.

WARNING: These endpoints are for administrative use only and should be properly secured in production.
All operations use HIPAA-compliant patient_id for data isolation and privacy.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from src.db.mongo_db import mongo_db as mongo_client
from src.db.neo4j_db import neo4j_db as neo4j_client
from src.db.milvus_db import milvus_db as milvus_client
from src.utils.logging import logger


class PatientDataSummary(BaseModel):
    """Summary of patient data across all databases."""
    patient_id: str
    mongo_records: int
    neo4j_nodes: int
    milvus_vectors: int
    last_activity: Optional[str] = None


class PatientListResponse(BaseModel):
    """Response model for listing patients."""
    patient_ids: List[str]
    total_count: int


class PatientDataResponse(BaseModel):
    """Response model for patient data retrieval."""
    patient_id: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None


class PatientDeletionResponse(BaseModel):
    """Response model for patient data deletion."""
    patient_id: str
    deleted: bool
    details: Dict[str, Any]
    errors: List[str] = []


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/patients/mongo", response_model=PatientListResponse)
async def list_mongo_patients():
    """List all patient IDs that have data in MongoDB."""
    try:
        if not mongo_client or not mongo_client._initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MongoDB not available"
            )
        
        patient_ids = await mongo_client.list_user_ids()
        return PatientListResponse(patient_ids=patient_ids, total_count=len(patient_ids))
        
    except Exception as e:
        logger.error(f"Failed to list MongoDB patients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve MongoDB patients: {str(e)}"
        )


@router.get("/patients/neo4j", response_model=PatientListResponse)
async def list_neo4j_patients():
    """List all patient IDs that have data in Neo4j."""
    try:
        if not neo4j_client or not neo4j_client._initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Neo4j not available"
            )
        
        patient_ids = neo4j_client.list_patient_ids()
        return PatientListResponse(patient_ids=patient_ids, total_count=len(patient_ids))
        
    except Exception as e:
        logger.error(f"Failed to list Neo4j patients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Neo4j patients: {str(e)}"
        )


@router.get("/patients/milvus", response_model=PatientListResponse)
async def list_milvus_patients():
    """List all patient IDs that have data in Milvus."""
    try:
        if not milvus_client or not milvus_client._initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Milvus not available"
            )
        
        patient_ids = milvus_client.list_user_ids()
        return PatientListResponse(patient_ids=patient_ids, total_count=len(patient_ids))
        
    except Exception as e:
        logger.error(f"Failed to list Milvus patients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Milvus patients: {str(e)}"
        )


@router.get("/patients/all")
async def list_all_patients():
    """List all patient IDs across all databases."""
    result = {}
    
    # MongoDB patients
    try:
        if mongo_client and mongo_client._initialized:
            mongo_patients = await mongo_client.list_user_ids()
            result["mongo"] = PatientListResponse(patient_ids=mongo_patients, total_count=len(mongo_patients))
        else:
            result["mongo"] = PatientListResponse(patient_ids=[], total_count=0)
    except Exception as e:
        logger.error(f"Failed to list MongoDB patients: {e}")
        result["mongo"] = PatientListResponse(patient_ids=[], total_count=0)
    
    # Neo4j patients
    try:
        if neo4j_client and neo4j_client._initialized:
            neo4j_patients = neo4j_client.list_patient_ids()
            result["neo4j"] = PatientListResponse(patient_ids=neo4j_patients, total_count=len(neo4j_patients))
        else:
            result["neo4j"] = PatientListResponse(patient_ids=[], total_count=0)
    except Exception as e:
        logger.error(f"Failed to list Neo4j patients: {e}")
        result["neo4j"] = PatientListResponse(patient_ids=[], total_count=0)
    
    # Milvus patients
    try:
        if milvus_client and milvus_client._initialized:
            milvus_patients = milvus_client.list_user_ids()
            result["milvus"] = PatientListResponse(patient_ids=milvus_patients, total_count=len(milvus_patients))
        else:
            result["milvus"] = PatientListResponse(patient_ids=[], total_count=0)
    except Exception as e:
        logger.error(f"Failed to list Milvus patients: {e}")
        result["milvus"] = PatientListResponse(patient_ids=[], total_count=0)
    
    return result


@router.get("/patient/{patient_id}/mongo", response_model=PatientDataResponse)
async def get_patient_mongo_data(patient_id: str):
    """Get patient's data from MongoDB."""
    try:
        if not mongo_client or not mongo_client._initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MongoDB not available"
            )
        
        # Get medical records
        medical_records = await mongo_client.get_medical_records(patient_id)
        
        # Get timeline events
        timeline_events = await mongo_client.get_timeline_events(patient_id)
        
        # Get PII data (if exists)
        pii_data = None
        try:
            pii_data = await mongo_client.get_user_pii(patient_id)
        except Exception as e:
            logger.warning(f"Could not retrieve PII for patient {patient_id}: {e}")
        
        data = {
            "medical_records": medical_records,
            "timeline_events": timeline_events,
            "pii_data": pii_data,
            "total_records": len(medical_records) if medical_records else 0,
            "total_events": len(timeline_events) if timeline_events else 0
        }
        
        return PatientDataResponse(
            patient_id=patient_id,
            success=True,
            data=data
        )
        
    except Exception as e:
        logger.error(f"Failed to get MongoDB data for patient {patient_id}: {e}")
        return PatientDataResponse(
            patient_id=patient_id,
            success=False,
            data={},
            error=str(e)
        )


@router.get("/patient/{patient_id}/neo4j", response_model=PatientDataResponse)
async def get_patient_neo4j_data(patient_id: str):
    """Get patient's data from Neo4j."""
    try:
        if not neo4j_client or not neo4j_client._initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Neo4j not available"
            )
        
        # Get body part severities
        severities = neo4j_client.get_body_part_severities(patient_id)
        
        # Get patient timeline
        timeline = neo4j_client.get_patient_timeline(patient_id, limit=50)
        
        # Get all body parts for this patient
        body_parts = []
        try:
            for body_part in severities.keys():
                history = neo4j_client.get_body_part_history(patient_id, body_part, limit=10)
                body_parts.append({
                    "name": body_part,
                    "severity": severities.get(body_part, 0),
                    "history": history
                })
        except Exception as e:
            logger.warning(f"Could not get body part details for patient {patient_id}: {e}")
        
        data = {
            "body_part_severities": severities,
            "timeline": timeline,
            "body_parts": body_parts,
            "total_body_parts": len(severities),
            "total_timeline_events": len(timeline) if timeline else 0
        }
        
        return PatientDataResponse(
            patient_id=patient_id,
            success=True,
            data=data
        )
        
    except Exception as e:
        logger.error(f"Failed to get Neo4j data for patient {patient_id}: {e}")
        return PatientDataResponse(
            patient_id=patient_id,
            success=False,
            data={},
            error=str(e)
        )


@router.get("/patient/{patient_id}/milvus", response_model=PatientDataResponse)
async def get_patient_milvus_data(patient_id: str):
    """Get patient's data from Milvus."""
    try:
        if not milvus_client or not milvus_client._initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Milvus not available"
            )
        
        # Get vector count for this patient
        # Note: Milvus doesn't have a direct way to get all vectors for a user
        # This is a placeholder implementation
        data = {
            "patient_id": patient_id,
            "vector_collections": [],
            "total_vectors": 0,
            "note": "Milvus vector details require specific queries"
        }
        
        return PatientDataResponse(
            patient_id=patient_id,
            success=True,
            data=data
        )
        
    except Exception as e:
        logger.error(f"Failed to get Milvus data for patient {patient_id}: {e}")
        return PatientDataResponse(
            patient_id=patient_id,
            success=False,
            data={},
            error=str(e)
        )


@router.get("/patient/{patient_id}/all")
async def get_patient_all_data(patient_id: str):
    """Get patient's data from all databases."""
    result = {
        "patient_id": patient_id,
        "mongo": None,
        "neo4j": None,
        "milvus": None
    }
    
    # Get MongoDB data
    try:
        mongo_response = await get_patient_mongo_data(patient_id)
        result["mongo"] = mongo_response.dict()
    except Exception as e:
        logger.error(f"Failed to get MongoDB data for patient {patient_id}: {e}")
        result["mongo"] = {"success": False, "error": str(e)}
    
    # Get Neo4j data
    try:
        neo4j_response = await get_patient_neo4j_data(patient_id)
        result["neo4j"] = neo4j_response.dict()
    except Exception as e:
        logger.error(f"Failed to get Neo4j data for patient {patient_id}: {e}")
        result["neo4j"] = {"success": False, "error": str(e)}
    
    # Get Milvus data
    try:
        milvus_response = await get_patient_milvus_data(patient_id)
        result["milvus"] = milvus_response.dict()
    except Exception as e:
        logger.error(f"Failed to get Milvus data for patient {patient_id}: {e}")
        result["milvus"] = {"success": False, "error": str(e)}
    
    return result


@router.delete("/patient/{patient_id}", response_model=PatientDeletionResponse)
async def delete_patient_data(patient_id: str):
    """Delete all patient data across all databases."""
    deletion_details = {}
    errors = []
    
    # Delete from MongoDB
    try:
        if mongo_client and mongo_client._initialized:
            mongo_result = await mongo_client.delete_user_data(patient_id)
            deletion_details["mongo"] = mongo_result
        else:
            deletion_details["mongo"] = {"deleted": False, "reason": "MongoDB not available"}
    except Exception as e:
        error_msg = f"MongoDB deletion failed: {str(e)}"
        errors.append(error_msg)
        deletion_details["mongo"] = {"deleted": False, "error": error_msg}
        logger.error(f"Failed to delete MongoDB data for patient {patient_id}: {e}")
    
    # Delete from Neo4j
    try:
        if neo4j_client and neo4j_client._initialized:
            neo4j_result = neo4j_client.delete_user_data(patient_id)
            deletion_details["neo4j"] = neo4j_result
        else:
            deletion_details["neo4j"] = {"deleted": False, "reason": "Neo4j not available"}
    except Exception as e:
        error_msg = f"Neo4j deletion failed: {str(e)}"
        errors.append(error_msg)
        deletion_details["neo4j"] = {"deleted": False, "error": error_msg}
        logger.error(f"Failed to delete Neo4j data for patient {patient_id}: {e}")
    
    # Delete from Milvus
    try:
        if milvus_client and milvus_client._initialized:
            milvus_result = milvus_client.delete_user_data(patient_id)
            deletion_details["milvus"] = milvus_result
        else:
            deletion_details["milvus"] = {"deleted": False, "reason": "Milvus not available"}
    except Exception as e:
        error_msg = f"Milvus deletion failed: {str(e)}"
        errors.append(error_msg)
        deletion_details["milvus"] = {"deleted": False, "error": error_msg}
        logger.error(f"Failed to delete Milvus data for patient {patient_id}: {e}")
    
    # Determine overall success
    deleted = len(errors) == 0
    
    if deleted:
        logger.info(f"Successfully deleted all data for patient {patient_id}")
    else:
        logger.warning(f"Partial deletion for patient {patient_id}: {errors}")
    
    return PatientDeletionResponse(
        patient_id=patient_id,
        deleted=deleted,
        details=deletion_details,
        errors=errors
    )


@router.get("/system/health")
async def system_health_check():
    """Check the health of all database systems."""
    health_status = {}
    overall_status = "healthy"
    
    # Check MongoDB
    try:
        if mongo_client and mongo_client._initialized:
            # Try a simple operation
            await mongo_client.list_user_ids()
            health_status["mongo"] = "healthy"
        else:
            health_status["mongo"] = "unavailable"
            overall_status = "degraded"
    except Exception as e:
        health_status["mongo"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    # Check Neo4j
    try:
        if neo4j_client and neo4j_client._initialized:
            # Try a simple operation
            neo4j_client.list_patient_ids()
            health_status["neo4j"] = "healthy"
        else:
            health_status["neo4j"] = "unavailable"
            overall_status = "degraded"
    except Exception as e:
        health_status["neo4j"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    # Check Milvus
    try:
        if milvus_client and milvus_client._initialized:
            # Try a simple operation
            milvus_client.list_user_ids()
            health_status["milvus"] = "healthy"
        else:
            health_status["milvus"] = "unavailable"
            overall_status = "degraded"
    except Exception as e:
        health_status["milvus"] = f"error: {str(e)}"
        overall_status = "degraded"
    
    return {
        "status": overall_status,
        "databases": health_status,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/stats/overview")
async def system_statistics():
    """Get system-wide statistics."""
    stats = {
        "total_patients": {},
        "system_health": {},
        "last_updated": datetime.now().isoformat()
    }
    
    # MongoDB stats
    try:
        if mongo_client and mongo_client._initialized:
            mongo_patients = await mongo_client.list_user_ids()
            stats["total_patients"]["mongo"] = len(mongo_patients)
            stats["system_health"]["mongo"] = "healthy"
        else:
            stats["total_patients"]["mongo"] = 0
            stats["system_health"]["mongo"] = "unavailable"
    except Exception as e:
        stats["total_patients"]["mongo"] = 0
        stats["system_health"]["mongo"] = f"error: {str(e)}"
    
    # Neo4j stats
    try:
        if neo4j_client and neo4j_client._initialized:
            neo4j_patients = neo4j_client.list_patient_ids()
            stats["total_patients"]["neo4j"] = len(neo4j_patients)
            stats["system_health"]["neo4j"] = "healthy"
        else:
            stats["total_patients"]["neo4j"] = 0
            stats["system_health"]["neo4j"] = "unavailable"
    except Exception as e:
        stats["total_patients"]["neo4j"] = 0
        stats["system_health"]["neo4j"] = f"error: {str(e)}"
    
    # Milvus stats
    try:
        if milvus_client and milvus_client._initialized:
            milvus_patients = milvus_client.list_user_ids()
            stats["total_patients"]["milvus"] = len(milvus_patients)
            stats["system_health"]["milvus"] = "healthy"
        else:
            stats["total_patients"]["milvus"] = 0
            stats["system_health"]["milvus"] = "unavailable"
    except Exception as e:
        stats["total_patients"]["milvus"] = 0
        stats["system_health"]["milvus"] = f"error: {str(e)}"
    
    return stats
