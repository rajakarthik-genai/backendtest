"""
Document upload and management endpoints
Handles medical document upload, processing, and status tracking
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from typing import List, Optional
import uuid
from datetime import datetime
import aiofiles
from pathlib import Path

from src.auth.dependencies import get_authenticated_patient_id
from src.models.document import (
    DocumentUploadResponse, PatientDocument, DocumentStatus,
    DocumentProcessingRequest
)
from src.core.config import settings
from src.core.exceptions import DocumentProcessingError, ValidationError
from src.db.models import Document as DBDocument
from src.db.mongodb import get_database
from src.db.neo4j import Neo4jConnection
from src.db.redis_db import get_redis
from src.auth.dependencies import get_current_user
from src.core.database import get_database_clients
from src.core.limiter import limiter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload", response_model=DocumentUploadResponse)
@limiter.limit("100/hour")
async def upload_medical_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    patient_id: str = Depends(get_authenticated_patient_id)
):
    """
    Upload medical documents for processing
    
    - Validates file type and size
    - Stores in MinIO
    - Queues for LLM-based extraction
    - Returns document ID for tracking
    """
    try:
        # Validate file
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_FILE_TYPES:
            raise ValidationError(
                f"File type {file_ext} not supported. Allowed: {settings.ALLOWED_FILE_TYPES}"
            )
        
        # Check file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > settings.MAX_FILE_SIZE:
            raise ValidationError(
                f"File too large. Maximum size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Generate document ID
        document_id = f"doc_{patient_id}_{uuid.uuid4().hex[:8]}"
        
        # Save to local storage (in production, use MinIO)
        upload_dir = settings.UPLOAD_DIR / patient_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / f"{document_id}{file_ext}"
        
        # Read and save file content
        content = await file.read()
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        # Create document record in MongoDB
        document = DBDocument(
            document_id=document_id,
            patient_id=patient_id,
            filename=file.filename,
            file_type=file_ext,
            file_size=file_size,
            status=DocumentStatus.PENDING,
            minio_path=str(file_path),
            uploaded_by=current_user["user_id"],
            uploaded_at=datetime.utcnow(),
            metadata={
                "content_type": file.content_type,
                "original_filename": file.filename
            }
        )
        
        # Save to MongoDB
        await db_clients["mongodb"].documents.insert_one(document.dict())
        
        # Create patient graph if not exists
        await db_clients["neo4j"].create_patient_graph(patient_id)
        
        # Add document to Neo4j graph
        await db_clients["neo4j"].add_document_to_graph(
            document_id, patient_id, file.filename
        )
        
        # Queue for processing
        processing_request = DocumentProcessingRequest(
            document_id=document_id,
            patient_id=patient_id,
            file_path=str(file_path),
            file_type=file_ext,
            priority="normal"
        )
        
        # Add to Redis queue
        await db_clients["redis"].enqueue_job({
            "job_type": "document_processing",
            "job_id": f"proc_{document_id}",
            "document_id": document_id,
            "patient_id": patient_id,
            "file_path": str(file_path),
            "file_type": file_ext,
            "priority": "normal"
        })
        
        # Log upload
        logger.info(f"Document uploaded: {document_id} for patient {patient_id}")
        
        return DocumentUploadResponse(
            document_id=document_id,
            patient_id=patient_id,
            status=DocumentStatus.PENDING,
            message=f"Document {file.filename} uploaded successfully and queued for processing",
            uploaded_at=datetime.utcnow(),
            estimated_processing_time=120  # 2 minutes estimate
        )
        
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
@limiter.limit("1000/hour")
async def get_patient_documents_status(
    request: Request,
    status_filter: Optional[DocumentStatus] = None,
    limit: int = 50,
    skip: int = 0,
    patient_id: str = Depends(get_authenticated_patient_id)
):
    """
    Get all documents for a patient with processing status
    
    Returns:
    - Document list with status
    - Extracted data summary
    - Affected body parts
    """
    try:
        # Build query
        query = {"patient_id": patient_id}
        if status_filter:
            query["status"] = status_filter
        
        # Get documents from MongoDB
        cursor = db_clients["mongodb"].documents.find(query).skip(skip).limit(limit)
        documents = await cursor.to_list(length=limit)
        
        # Convert to response model
        patient_documents = []
        for doc in documents:
            # Get extraction summary if processed
            extracted_summary = None
            affected_body_parts = None
            
            if doc["status"] == DocumentStatus.COMPLETED:
                # Get extraction results from Neo4j
                neo4j = db_clients["neo4j"]
                result = await neo4j.execute_query("""
                    MATCH (d:Document {document_id: $document_id})-[:EXTRACTED]->(e:Entity)
                    OPTIONAL MATCH (e)-[:AFFECTS]->(bp:BodyPart)
                    RETURN 
                        count(DISTINCT e) as entity_count,
                        collect(DISTINCT e.type) as entity_types,
                        collect(DISTINCT bp.name) as body_parts,
                        avg(e.severity) as avg_severity
                """, {"document_id": doc["document_id"]})
                
                if result:
                    record = result[0]
                    extracted_summary = {
                        "entities_found": record["entity_count"],
                        "entity_types": record["entity_types"],
                        "average_severity": record["avg_severity"]
                    }
                    affected_body_parts = record["body_parts"]
            
            patient_doc = PatientDocument(
                document_id=doc["document_id"],
                patient_id=doc["patient_id"],
                filename=doc["filename"],
                file_type=doc["file_type"],
                status=doc["status"],
                uploaded_at=doc["uploaded_at"],
                processed_at=doc.get("processed_at"),
                extracted_data_summary=extracted_summary,
                affected_body_parts=affected_body_parts,
                error_message=doc.get("error_message")
            )
            patient_documents.append(patient_doc)
        
        return patient_documents
        
    except Exception as e:
        logger.error(f"Failed to get document status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/document/{document_id}")
@limiter.limit("1000/hour")
async def get_document_details(
    request: Request,
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_database_clients)
):
    """
    Get detailed information about a specific document
    Including full extraction results
    """
    try:
        # Get document from MongoDB
        document = await db_clients["mongodb"].documents.find_one(
            {"document_id": document_id}
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check access permission
        if document["patient_id"] != current_user.get("patient_id") and not current_user.get("is_provider"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get detailed extraction results if completed
        extraction_details = None
        if document["status"] == DocumentStatus.COMPLETED:
            neo4j = db_clients["neo4j"]
            
            # Get all extracted entities
            entities_result = await neo4j.execute_query("""
                MATCH (d:Document {document_id: $document_id})-[:EXTRACTED]->(e:Entity)
                OPTIONAL MATCH (e)-[:AFFECTS]->(bp:BodyPart)
                RETURN e, collect(bp.name) as body_parts
                ORDER BY e.date DESC, e.severity DESC
            """, {"document_id": document_id})
            
            # Get timeline events
            timeline_result = await neo4j.execute_query("""
                MATCH (d:Document {document_id: $document_id})-[:CONTAINS_EVENT]->(ev:Event)
                OPTIONAL MATCH (ev)-[:AFFECTS]->(bp:BodyPart)
                RETURN ev, collect(bp.name) as body_parts
                ORDER BY ev.date
            """, {"document_id": document_id})
            
            extraction_details = {
                "entities": [
                    {
                        "type": record["e"]["type"],
                        "text": record["e"]["text"],
                        "severity": record["e"].get("severity"),
                        "date": record["e"].get("date"),
                        "body_parts": record["body_parts"],
                        "confidence": record["e"].get("confidence", 1.0)
                    }
                    for record in entities_result
                ],
                "timeline_events": [
                    {
                        "event_type": record["ev"]["event_type"],
                        "description": record["ev"]["description"],
                        "date": record["ev"]["date"],
                        "body_parts": record["body_parts"]
                    }
                    for record in timeline_result
                ]
            }
        
        return {
            **document,
            "extraction_details": extraction_details
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reprocess/{document_id}")
@limiter.limit("10/hour")
async def reprocess_document(
    request: Request,
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_database_clients)
):
    """
    Reprocess a document that failed or needs updating
    """
    try:
        # Get document
        document = await db_clients["mongodb"].documents.find_one(
            {"document_id": document_id}
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check permission
        if document["patient_id"] != current_user.get("patient_id") and not current_user.get("is_provider"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update status
        await db_clients["mongodb"].documents.update_one(
            {"document_id": document_id},
            {"$set": {"status": DocumentStatus.PENDING, "error_message": None}}
        )
        
        # Re-queue for processing
        await db_clients["redis"].enqueue_job({
            "job_type": "document_processing",
            "job_id": f"reproc_{document_id}",
            "document_id": document_id,
            "patient_id": document["patient_id"],
            "file_path": document["minio_path"],
            "file_type": document["file_type"],
            "priority": "high"  # Higher priority for reprocessing
        }, priority="high")
        
        return {
            "message": "Document queued for reprocessing",
            "document_id": document_id,
            "status": DocumentStatus.PENDING
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reprocess document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{document_id}")
@limiter.limit("50/hour")
async def delete_document(
    request: Request,
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_database_clients)
):
    """
    Delete a document and all associated data
    """
    try:
        # Get document
        document = await db_clients["mongodb"].documents.find_one(
            {"document_id": document_id}
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check permission
        if document["patient_id"] != current_user.get("patient_id") and not current_user.get("is_provider"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete file from storage
        file_path = Path(document["minio_path"])
        if file_path.exists():
            file_path.unlink()
        
        # Delete from Neo4j
        neo4j = db_clients["neo4j"]
        await neo4j.execute_query("""
            MATCH (d:Document {document_id: $document_id})
            OPTIONAL MATCH (d)-[r]->(n)
            DELETE r, n, d
        """, {"document_id": document_id})
        
        # Delete from MongoDB
        await db_clients["mongodb"].documents.delete_one({"document_id": document_id})
        
        logger.info(f"Document deleted: {document_id}")
        
        return {"message": "Document deleted successfully", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
