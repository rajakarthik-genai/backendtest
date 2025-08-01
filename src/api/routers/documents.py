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

from src.models.document import (
    DocumentUploadResponse, PatientDocument, DocumentStatus,
    DocumentProcessingRequest
)
from src.core.config import settings
from src.core.exceptions import DocumentProcessingError, ValidationError
from src.db.models import Document
from src.db.mongodb import get_database
from src.db.neo4j import Neo4jConnection
from src.db.redis_db import get_redis
from src.api.dependencies import get_current_user, get_db_clients, get_authenticated_patient_id
from src.core.limiter import limiter
from src.services.cache_service import CacheService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload", response_model=DocumentUploadResponse)
@limiter.limit("100/hour")
async def upload_medical_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Medical document file to upload"),
    patient_id: str = Depends(get_authenticated_patient_id),
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Upload medical documents for processing
    
    - Validates file type and size
    - Stores in MinIO
    - Queues for LLM-based extraction
    - Returns document ID for tracking
    """
    try:
        if db_clients.get("mongodb") is None:
            raise HTTPException(status_code=503, detail="MongoDB not available")
            
        mongodb = db_clients["mongodb"]
        if mongodb is None:
            raise HTTPException(status_code=503, detail="MongoDB connection not available")
            
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
        
        # Read file content
        content = await file.read()
        
        # Save to MinIO (preferred) or local storage (fallback)
        minio_client = None
        object_path = None
        
        try:
            # Temporarily disabled until container rebuild
            # from src.db.minio_client import get_minio_client, generate_object_path
            # minio_client = get_minio_client()
            
            # Force fallback to local storage for now
            raise Exception("MinIO temporarily disabled")
                
        except Exception as e:
            logger.warning(f"MinIO upload failed, using local storage: {e}")
            # Fallback to local storage
            upload_dir = settings.UPLOAD_DIR / patient_id
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / f"{document_id}{file_ext}"
            
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
            
            file_path_str = str(file_path)
        
        # Create document record in MongoDB
        document = Document(
            document_id=document_id,
            patient_id=patient_id,
            filename=file.filename,
            file_type=file_ext,
            file_size=file_size,
            status=DocumentStatus.PENDING,
            minio_path=file_path_str,
            uploaded_by=current_user["user_id"],
            uploaded_at=datetime.utcnow(),
            metadata={
                "content_type": file.content_type,
                "original_filename": file.filename
            }
        )
        
        # Save to MongoDB
        await mongodb.documents.insert_one(document.model_dump())
        
        # Create patient graph if not exists (Neo4j methods are synchronous)
        if db_clients.get("neo4j") is not None:
            db_clients["neo4j"].create_patient_graph(patient_id)
            
            # Add document to Neo4j graph
            db_clients["neo4j"].add_document_to_graph(
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
        
        # Add to Redis queue (if available)
        if db_clients.get("redis") is not None:
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
        
        # Invalidate patient document cache
        cache_service = CacheService()
        await cache_service.initialize()
        await cache_service.invalidate_patient_cache(patient_id)
        
        return DocumentUploadResponse(
            document_id=document_id,
            patient_id=patient_id,
            status=DocumentStatus.PENDING,
            message=f"Document {file.filename} uploaded successfully and queued for processing",
            uploaded_at=datetime.utcnow(),
            estimated_processing_time=120  # 2 minutes estimate
        )
        
    except Exception as e:
        logger.error(f"Error in upload_medical_document: {e}")
        raise HTTPException(status_code=503, detail="Database error")

@router.get("/status")
@limiter.limit("1000/hour")
async def get_patient_documents_status(
    request: Request,
    status_filter: Optional[DocumentStatus] = None,
    limit: int = 50,
    skip: int = 0,
    patient_id: str = Depends(get_authenticated_patient_id),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get all documents for a patient with processing status
    
    Returns:
    - Document list with status
    - Extracted data summary
    - Affected body parts
    """
    try:
        if db_clients.get("mongodb") is None:
            raise HTTPException(status_code=503, detail="MongoDB not available")
            
        mongodb = db_clients["mongodb"]
        if mongodb is None:
            raise HTTPException(status_code=503, detail="MongoDB connection not available")
        
        # Initialize cache service
        cache_service = CacheService()
        await cache_service.initialize()
        
        # Try to get from cache first
        cache_key = f"documents:status:{patient_id}:{status_filter}:{limit}:{skip}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached document status for patient {patient_id}")
            return cached_result
        
        # Build query
        query = {"patient_id": patient_id}
        if status_filter:
            query["status"] = status_filter
        
        # Get documents from MongoDB
        cursor = mongodb.documents.find(query).skip(skip).limit(limit)
        documents = await cursor.to_list(length=limit)
        
        # Convert to response model
        patient_documents = []
        for doc in documents:
            # Get extraction summary if processed
            extracted_summary = None
            affected_body_parts = None
            
            if doc["status"] == DocumentStatus.COMPLETED and db_clients.get("neo4j") is not None:
                # Get extraction results from Neo4j (synchronous call)
                neo4j = db_clients["neo4j"]
                result = neo4j.execute_query("""
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
                upload_date=doc["uploaded_at"],  # Map to required field
                processing_status=doc["status"],  # Map to required field
                processed_at=doc.get("processed_at"),
                extracted_data_summary=extracted_summary,
                affected_body_parts=affected_body_parts,
                error_message=doc.get("error_message"),
                file_size=doc.get("file_size"),
                content_type=doc.get("metadata", {}).get("content_type")
            )
            patient_documents.append(patient_doc)
        
        # Cache the result for 5 minutes
        await cache_service.set(cache_key, patient_documents, ttl=300)
        
        return patient_documents
        
    except Exception as e:
        logger.error(f"Error in get_patient_documents_status: {e}")
        raise HTTPException(status_code=503, detail="Database error")

@router.get("/document/{document_id}")
@limiter.limit("1000/hour")
async def get_document_details(
    request: Request,
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get detailed information about a specific document
    Including full extraction results
    """
    try:
        if db_clients.get("mongodb") is None:
            raise HTTPException(status_code=503, detail="MongoDB not available")
            
        mongodb = db_clients["mongodb"]
        if mongodb is None:
            raise HTTPException(status_code=503, detail="MongoDB connection not available")
        
        # Initialize cache service
        cache_service = CacheService()
        await cache_service.initialize()
        
        # Try to get from cache first
        cache_key = f"document:details:{document_id}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            # Still need to check access permission
            if cached_result["patient_id"] != current_user.get("patient_id") and not current_user.get("is_provider"):
                raise HTTPException(status_code=403, detail="Access denied")
            logger.info(f"Returning cached document details for {document_id}")
            return cached_result
            
        # Get document from MongoDB
        document = await mongodb.documents.find_one(
            {"document_id": document_id}
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Convert MongoDB document to JSON-serializable format
        def convert_mongo_doc(doc):
            """Convert MongoDB document to JSON-serializable dict"""
            if doc is None:
                return None
            # Convert ObjectId to string and handle other non-serializable types
            result = {}
            for key, value in doc.items():
                if hasattr(value, '__str__') and key == '_id':
                    result[key] = str(value)
                elif hasattr(value, 'isoformat'):  # datetime objects
                    result[key] = value.isoformat()
                else:
                    result[key] = value
            return result
        
        document = convert_mongo_doc(document)
        
        # Check access permission
        if document["patient_id"] != current_user.get("patient_id") and not current_user.get("is_provider"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get detailed extraction results if completed
        extraction_details = None
        if document["status"] == DocumentStatus.COMPLETED and db_clients.get("neo4j") is not None:
            neo4j = db_clients["neo4j"]
            
            # Get all extracted entities (synchronous calls)
            entities_result = neo4j.execute_query("""
                MATCH (d:Document {document_id: $document_id})-[:EXTRACTED]->(e:Entity)
                OPTIONAL MATCH (e)-[:AFFECTS]->(bp:BodyPart)
                RETURN e, collect(bp.name) as body_parts
                ORDER BY e.date DESC, e.severity DESC
            """, {"document_id": document_id})
            
            # Get timeline events
            timeline_result = neo4j.execute_query("""
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
        
        document_details = {
            **document,
            "extraction_details": extraction_details
        }
        
        # Cache the result for 10 minutes (documents don't change often)
        await cache_service.set(cache_key, document_details, ttl=600)
        
        return document_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_document_details: {e}")
        raise HTTPException(status_code=503, detail="Database error")

@router.post("/reprocess/{document_id}")
@limiter.limit("10/hour")
async def reprocess_document(
    request: Request,
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Reprocess a document that failed or needs updating
    """
    try:
        if db_clients.get("mongodb") is None:
            raise HTTPException(status_code=503, detail="MongoDB not available")
            
        mongodb = db_clients["mongodb"]
        # Get document
        document = await mongodb.documents.find_one(
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
        logger.error(f"Error in reprocess_document: {e}")
        raise HTTPException(status_code=503, detail="Database error")

@router.delete("/delete/{document_id}")
@limiter.limit("50/hour")
async def delete_document(
    request: Request,
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Delete a document and all associated data
    """
    try:
        if db_clients.get("mongodb") is None:
            raise HTTPException(status_code=503, detail="MongoDB not available")
            
        mongodb = db_clients["mongodb"]
        if mongodb is None:
            raise HTTPException(status_code=503, detail="MongoDB connection not available")
            
        # Get document
        document = await mongodb.documents.find_one(
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
        
        # Delete from Neo4j (synchronous call)
        neo4j = db_clients["neo4j"]
        if neo4j is not None:
            neo4j.execute_query("""
                MATCH (d:Document {document_id: $document_id})
                OPTIONAL MATCH (d)-[r]->(n)
                DELETE r, n, d
            """, {"document_id": document_id})
        
        # Delete from MongoDB
        await mongodb.documents.delete_one({"document_id": document_id})
        
        logger.info(f"Document deleted: {document_id}")
        
        return {"message": "Document deleted successfully", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_document: {e}")
        raise HTTPException(status_code=503, detail="Database error")


@router.get("/")
@limiter.limit("1000/hour")
async def list_documents(
    request: Request,
    patient_id: str = Depends(get_authenticated_patient_id),
    status_filter: Optional[DocumentStatus] = None,
    limit: int = 50,
    skip: int = 0,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    List all documents for the authenticated patient
    
    Returns:
    - Simple list of documents with basic info
    - Status and metadata
    """
    try:
        if db_clients.get("mongodb") is None:
            raise HTTPException(status_code=503, detail="MongoDB not available")
            
        mongodb = db_clients["mongodb"]
        if mongodb is None:
            raise HTTPException(status_code=503, detail="MongoDB connection not available")
        
        # Build query
        query = {"patient_id": patient_id}
        if status_filter:
            query["status"] = status_filter
        
        # Get documents from MongoDB
        cursor = mongodb.documents.find(query).skip(skip).limit(limit)
        documents = await cursor.to_list(length=limit)
        
        # Return simple document list with safety checks for missing fields
        return [
            {
                "document_id": doc.get("document_id", "unknown"),
                "filename": doc.get("filename", doc.get("original_filename", "unknown.txt")),
                "file_type": doc.get("file_type", "unknown"),
                "file_size": doc.get("file_size", 0),
                "status": doc.get("status", "unknown"),
                "uploaded_at": doc.get("uploaded_at"),
                "processed_at": doc.get("processed_at")
            }
            for doc in documents
            if "document_id" in doc  # Only include documents with valid IDs
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in list_documents: {e}")
        raise HTTPException(status_code=503, detail="Database error")


@router.get("/{document_id}/status")
@limiter.limit("1000/hour")
async def get_document_status(
    request: Request,
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db_clients: dict = Depends(get_db_clients)
):
    """
    Get the processing status of a specific document
    
    Returns:
    - Document processing status
    - Progress information
    - Error details if failed
    """
    try:
        if db_clients.get("mongodb") is None:
            raise HTTPException(status_code=503, detail="MongoDB not available")
            
        mongodb = db_clients["mongodb"]
        if mongodb is None:
            raise HTTPException(status_code=503, detail="MongoDB connection not available")
        
        # Get document from MongoDB
        document = await mongodb.documents.find_one(
            {"document_id": document_id}
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check access permission
        if document["patient_id"] != current_user.get("patient_id") and not current_user.get("is_provider"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare status response
        status_response = {
            "document_id": document_id,
            "status": document.get("status", "unknown"),
            "progress": 100 if document.get("status") == DocumentStatus.COMPLETED else 0,
            "filename": document.get("filename", "unknown"),
            "uploaded_at": document.get("uploaded_at"),
            "processed_at": document.get("processed_at"),
            "error_message": document.get("error_message"),
            "file_size": document.get("file_size", 0),
            "processing_started_at": document.get("processing_started_at"),
            "estimated_completion": None
        }
        
        # Add progress estimation for pending/processing documents
        if document.get("status") == DocumentStatus.PENDING:
            status_response["progress"] = 5
            status_response["estimated_completion"] = "2-3 minutes"
        elif document.get("status") == DocumentStatus.PROCESSING:
            status_response["progress"] = 50
            status_response["estimated_completion"] = "1-2 minutes"
        elif document.get("status") == DocumentStatus.FAILED:
            status_response["progress"] = 0
            
        return status_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_document_status: {e}")
        raise HTTPException(status_code=503, detail="Database error")
