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


@router.get("/patients/neo4j", response_model=UserListResponse)
async def list_neo4j_patients():
    """List all patient IDs that have data in Neo4j."""
    try:
        if not neo4j_client or not neo4j_client._initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Neo4j not available"
            )
        
        patient_ids = neo4j_client.list_patient_ids()
        return UserListResponse(user_ids=patient_ids, total_count=len(user_ids))
        
    except Exception as e:
        logger.error(f"Failed to list Neo4j patients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Neo4j patients: {str(e)}"
        )


@router.get("/patients/milvus", response_model=UserListResponse)
async def list_milvus_patients():
    """List all patient IDs that have data in Milvus."""
    try:
        if not milvus_client or not milvus_client._initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Milvus not available"
            )
        
        patient_ids = milvus_client.list_user_ids()
        return UserListResponse(user_ids=patient_ids, total_count=len(user_ids))
        
    except Exception as e:
        logger.error(f"Failed to list Milvus patients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Milvus patients: {str(e)}"
        )


@router.get("/patients/all", response_model=Dict[str, UserListResponse])
async def list_all_patients():
    """List all patient IDs across all databases."""
    try:
        result = {}
        
        # Get users from each database
        if mongo_client and mongo_client._initialized:
            try:
                mongo_patients = await mongo_client.list_user_ids()
                result["mongo"] = UserListResponse(user_ids=mongo_users, total_count=len(mongo_users))
            except Exception as e:
                logger.error(f"MongoDB user listing failed: {e}")
                result["mongo"] = UserListResponse(user_ids=[], total_count=0)
        
        if neo4j_client and neo4j_client._initialized:
            try:
                neo4j_patients = neo4j_client.list_patient_ids()
                result["neo4j"] = UserListResponse(user_ids=neo4j_users, total_count=len(neo4j_users))
            except Exception as e:
                logger.error(f"Neo4j user listing failed: {e}")
                result["neo4j"] = UserListResponse(user_ids=[], total_count=0)
        
        if milvus_client and milvus_client._initialized:
            try:
                milvus_patients = milvus_client.list_user_ids()
                result["milvus"] = UserListResponse(user_ids=milvus_users, total_count=len(milvus_users))
            except Exception as e:
                logger.error(f"Milvus user listing failed: {e}")
                result["milvus"] = UserListResponse(user_ids=[], total_count=0)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list all users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users from all databases: {str(e)}"
        )


@router.get("/user/{patient_id}/mongo", response_model=UserDataResponse)
async def get_patient_mongo_data(patient_id: str):
    """Retrieve all MongoDB data for a specific user."""
    try:
        if not mongo_client or not mongo_client._initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MongoDB not available"
            )
        
        # Get all medical records for the user
        medical_records = await mongo_client.get_medical_records(patient_id)
        
        # Get timeline events
        timeline_events = await mongo_client.get_timeline_events(patient_id)
        
        # Get user PII (if available)
        pii_data = None
        try:
            pii_data = await mongo_client.get_user_pii(user_id)
        except Exception as e:
            logger.warning(f"Could not retrieve PII for user {patient_id}: {e}")
        
        # Get document metadata
        doc_metadata = []
        try:
            doc_metadata = await mongo_client.list_user_document_metadata(patient_id)
        except Exception as e:
            logger.warning(f"Could not retrieve document metadata for user {patient_id}: {e}")
        
        data = {
            "medical_records": medical_records,
            "timeline_events": timeline_events,
            "pii_data": pii_data,
            "document_metadata": doc_metadata,
            "counts": {
                "medical_records": len(medical_records) if medical_records else 0,
                "timeline_events": len(timeline_events) if timeline_events else 0,
                "documents": len(doc_metadata) if doc_metadata else 0
            }
        }
        
        return UserDataResponse(user_id=patient_id, success=True, data=data)
        
    except Exception as e:
        logger.error(f"Failed to retrieve MongoDB data for user {patient_id}: {e}")
        return UserDataResponse(
            user_id=patient_id, 
            success=False, 
            data={}, 
            error=str(e)
        )


@router.get("/user/{patient_id}/neo4j", response_model=UserDataResponse)
async def get_patient_neo4j_data(patient_id: str):
    """Retrieve all Neo4j data for a specific user."""
    try:
        if not neo4j_client or not neo4j_client._initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Neo4j not available"
            )
        
        # Get patient timeline
        timeline = neo4j_client.get_patient_timeline(patient_id)
        
        # Get body part severities
        body_part_severities = neo4j_client.get_body_part_severities(patient_id)
        
        # Get body part history for each part
        body_part_history = {}
        for body_part, severity_info in body_part_severities.items():
            try:
                history = neo4j_client.get_body_part_history(patient_id, body_part)
                body_part_history[body_part] = history
            except Exception as e:
                logger.warning(f"Could not get history for {body_part}: {e}")
                body_part_history[body_part] = []
        
        data = {
            "timeline": timeline,
            "body_part_severities": body_part_severities,
            "body_part_history": body_part_history,
            "counts": {
                "events": len(timeline) if timeline else 0,
                "body_parts": len(body_part_severities) if body_part_severities else 0
            }
        }
        
        return UserDataResponse(user_id=patient_id, success=True, data=data)
        
    except Exception as e:
        logger.error(f"Failed to retrieve Neo4j data for user {patient_id}: {e}")
        return UserDataResponse(
            user_id=patient_id, 
            success=False, 
            data={}, 
            error=str(e)
        )


@router.get("/user/{patient_id}/milvus", response_model=UserDataResponse)
async def get_patient_milvus_data(patient_id: str):
    """Retrieve all Milvus data for a specific user."""
    try:
        if not milvus_client or not milvus_client._initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Milvus not available"
            )
        
        # Get all documents for the user
        user_documents = milvus_client.get_user_documents(patient_id, limit=1000)
        
        # Group by document_id for easier viewing
        documents_by_id = {}
        total_vectors = 0
        
        for doc in user_documents:
            doc_id = doc.get("document_id", "unknown")
            if doc_id not in documents_by_id:
                documents_by_id[doc_id] = []
            documents_by_id[doc_id].append(doc)
            total_vectors += 1
        
        data = {
            "documents": documents_by_id,
            "raw_vectors": user_documents,
            "counts": {
                "total_vectors": total_vectors,
                "unique_documents": len(documents_by_id)
            }
        }
        
        return UserDataResponse(user_id=patient_id, success=True, data=data)
        
    except Exception as e:
        logger.error(f"Failed to retrieve Milvus data for user {patient_id}: {e}")
        return UserDataResponse(
            user_id=patient_id, 
            success=False, 
            data={}, 
            error=str(e)
        )


@router.get("/user/{patient_id}/all", response_model=Dict[str, UserDataResponse])
async def get_patient_all_data(patient_id: str):
    """Retrieve all data for a specific user across all databases."""
    try:
        result = {}
        
        # Get data from each database
        if mongo_client and mongo_client._initialized:
            try:
                mongo_response = await get_patient_mongo_data(patient_id)
                result["mongo"] = mongo_response
            except Exception as e:
                logger.error(f"MongoDB data retrieval failed for user {patient_id}: {e}")
                result["mongo"] = UserDataResponse(
                    user_id=patient_id, success=False, data={}, error=str(e)
                )
        
        if neo4j_client and neo4j_client._initialized:
            try:
                neo4j_response = await get_patient_neo4j_data(patient_id)
                result["neo4j"] = neo4j_response
            except Exception as e:
                logger.error(f"Neo4j data retrieval failed for user {patient_id}: {e}")
                result["neo4j"] = UserDataResponse(
                    user_id=patient_id, success=False, data={}, error=str(e)
                )
        
        if milvus_client and milvus_client._initialized:
            try:
                milvus_response = await get_patient_milvus_data(patient_id)
                result["milvus"] = milvus_response
            except Exception as e:
                logger.error(f"Milvus data retrieval failed for user {patient_id}: {e}")
                result["milvus"] = UserDataResponse(
                    user_id=patient_id, success=False, data={}, error=str(e)
                )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to retrieve all data for user {patient_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve patient data: {str(e)}"
        )


@router.delete("/user/{patient_id}", response_model=UserDeletionResponse)
async def delete_patient_data(patient_id: str):
    """Delete all data for a specific user across all databases."""
    try:
        deleted = {"mongo": False, "neo4j": False, "milvus": False}
        errors = []
        details = {}
        
        # MongoDB deletion
        if mongo_client and mongo_client._initialized:
            try:
                deletion_result = await mongo_client.delete_patient_data(patient_id)
                deleted["mongo"] = deletion_result.get("success", False)
                details["mongo"] = deletion_result
                logger.info(f"MongoDB data deleted for user {patient_id}")
            except Exception as e:
                error_msg = f"MongoDB deletion failed: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                details["mongo"] = {"success": False, "error": str(e)}
        
        # Neo4j deletion
        if neo4j_client and neo4j_client._initialized:
            try:
                deletion_result = neo4j_client.delete_patient_data(patient_id)
                deleted["neo4j"] = deletion_result
                details["neo4j"] = {"success": deletion_result}
                logger.info(f"Neo4j data deleted for user {patient_id}")
            except Exception as e:
                error_msg = f"Neo4j deletion failed: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                details["neo4j"] = {"success": False, "error": str(e)}
        
        # Milvus deletion
        if milvus_client and milvus_client._initialized:
            try:
                deletion_result = milvus_client.delete_patient_data(patient_id)
                deleted["milvus"] = deletion_result
                details["milvus"] = {"success": deletion_result}
                logger.info(f"Milvus data deleted for user {patient_id}")
            except Exception as e:
                error_msg = f"Milvus deletion failed: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
                details["milvus"] = {"success": False, "error": str(e)}
        
        success = all(deleted.values())
        
        return UserDeletionResponse(
            user_id=patient_id,
            deleted=success,
            details=details,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Failed to delete patient data for {patient_id}: {e}")
        return UserDeletionResponse(
            user_id=patient_id,
            deleted=False,
            details={},
            errors=[f"General deletion failure: {str(e)}"]
        )


@router.get("/system/health")
async def system_health():
    """Get the health status of all database systems."""
    try:
        health = {
            "mongo": {"available": False, "initialized": False},
            "neo4j": {"available": False, "initialized": False},
            "milvus": {"available": False, "initialized": False}
        }
        
        # Check MongoDB
        if mongo_client:
            health["mongo"]["available"] = True
            health["mongo"]["initialized"] = mongo_client._initialized
            if mongo_client._initialized:
                try:
                    # Test connection
                    await mongo_client.client.admin.command('ping')
                    health["mongo"]["status"] = "healthy"
                except Exception as e:
                    health["mongo"]["status"] = f"error: {e}"
        
        # Check Neo4j
        if neo4j_client:
            health["neo4j"]["available"] = True
            health["neo4j"]["initialized"] = neo4j_client._initialized
            if neo4j_client._initialized:
                try:
                    # Test connection
                    with neo4j_client.driver.session() as session:
                        session.run("RETURN 1")
                    health["neo4j"]["status"] = "healthy"
                except Exception as e:
                    health["neo4j"]["status"] = f"error: {e}"
        
        # Check Milvus
        if milvus_client:
            health["milvus"]["available"] = True
            health["milvus"]["initialized"] = milvus_client._initialized
            if milvus_client._initialized:
                try:
                    # Test connection
                    milvus_client.collection.describe()
                    health["milvus"]["status"] = "healthy"
                except Exception as e:
                    health["milvus"]["status"] = f"error: {e}"
        
        return health
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/stats/overview")
async def get_system_stats():
    """Get overall system statistics."""
    try:
        stats = {
            "timestamp": str(datetime.utcnow()),
            "databases": {}
        }
        
        # MongoDB stats
        if mongo_client and mongo_client._initialized:
            try:
                mongo_patients = await mongo_client.list_user_ids()
                stats["databases"]["mongo"] = {
                    "total_users": len(mongo_users),
                    "status": "connected"
                }
            except Exception as e:
                stats["databases"]["mongo"] = {
                    "total_users": 0,
                    "status": f"error: {e}"
                }
        
        # Neo4j stats
        if neo4j_client and neo4j_client._initialized:
            try:
                neo4j_patients = neo4j_client.list_patient_ids()
                stats["databases"]["neo4j"] = {
                    "total_users": len(neo4j_users),
                    "status": "connected"
                }
            except Exception as e:
                stats["databases"]["neo4j"] = {
                    "total_users": 0,
                    "status": f"error: {e}"
                }
        
        # Milvus stats
        if milvus_client and milvus_client._initialized:
            try:
                milvus_patients = milvus_client.list_user_ids()
                stats["databases"]["milvus"] = {
                    "total_users": len(milvus_users),
                    "status": "connected"
                }
            except Exception as e:
                stats["databases"]["milvus"] = {
                    "total_users": 0,
                    "status": f"error: {e}"
                }
        
        return stats
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stats retrieval failed: {str(e)}"
        )
