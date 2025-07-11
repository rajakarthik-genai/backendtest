"""
Document processing endpoints using CrewAI multi-agent system.
"""

import os
import uuid
import tempfile
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, Field

from src.utils.logging import logger, log_user_action
from src.auth.dependencies import CurrentUser
from src.agents.crew_agents.medical_crew import MedicalDocumentCrew, process_medical_document

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentProcessingResponse(BaseModel):
    """Response model for document processing."""
    document_id: str = Field(description="Unique document identifier")
    status: str = Field(description="Processing status")
    message: str = Field(description="Status message")
    processing_summary: Optional[dict] = Field(None, description="Processing summary if completed")


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    document_id: str = Field(description="Unique document identifier")
    filename: str = Field(description="Original filename")
    file_size: int = Field(description="File size in bytes")
    status: str = Field(description="Upload status")
    processing_started: bool = Field(description="Whether processing has started")


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF document to process"),
    document_title: Optional[str] = Form(None, description="Document title or type"),
    process_immediately: bool = Form(True, description="Start processing immediately")
):
    """
    Upload a medical document for processing.
    
    Supports:
    - PDF files (with OCR for scanned documents)
    - Automatic text extraction and medical entity recognition
    - Storage across MongoDB, Neo4j, and Milvus
    - Patient data isolation
    """
    try:
        user_id = current_user.user_id
        
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Check file size (50MB limit)
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(status_code=400, detail="File too large (maximum 50MB)")
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Generate document ID
        document_id = f"doc_{user_id}_{int(datetime.utcnow().timestamp())}_{str(uuid.uuid4())[:8]}"
        
        # Save uploaded file temporarily
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"{document_id}.pdf")
        
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_content)
        
        # Prepare metadata
        metadata = {
            "original_filename": file.filename,
            "file_size": file_size,
            "document_title": document_title,
            "upload_timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id
        }
        
        logger.info(f"Document uploaded: {document_id} ({file.filename}, {file_size} bytes)")
        
        # Log user action
        log_user_action(
            user_id,
            "document_uploaded",
            {
                "document_id": document_id,
                "filename": file.filename,
                "file_size": file_size,
                "document_title": document_title
            }
        )
        
        # Start processing if requested
        if process_immediately:
            background_tasks.add_task(
                process_document_background,
                user_id,
                document_id,
                temp_file_path,
                metadata
            )
            processing_started = True
        else:
            processing_started = False
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=file_size,
            status="uploaded",
            processing_started=processing_started
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail="Document upload failed")


@router.post("/process/{document_id}", response_model=DocumentProcessingResponse)
async def process_document(
    document_id: str,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks
):
    """
    Start processing an uploaded document.
    
    This triggers the complete CrewAI pipeline:
    1. Document Reader: Extract text with OCR support
    2. Clinical Extractor: Extract medical entities and relationships
    3. Vector Embedder: Generate embeddings for semantic search
    4. Storage Coordinator: Store data across all databases
    """
    try:
        user_id = current_user.user_id
        
        # Check if document exists (this would need to be implemented based on your storage)
        # For now, we'll assume the document path exists
        temp_file_path = os.path.join(tempfile.gettempdir(), f"{document_id}.pdf")
        
        if not os.path.exists(temp_file_path):
            raise HTTPException(
                status_code=404, 
                detail="Document not found or already processed"
            )
        
        # Start background processing
        background_tasks.add_task(
            process_document_background,
            user_id,
            document_id,
            temp_file_path,
            {}
        )
        
        logger.info(f"Started processing document {document_id} for user {user_id[:8]}...")
        
        return DocumentProcessingResponse(
            document_id=document_id,
            status="processing",
            message="Document processing started in background"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start document processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to start document processing")


@router.get("/status/{document_id}", response_model=DocumentProcessingResponse)
async def get_processing_status(
    document_id: str,
    current_user: CurrentUser
):
    """
    Get the processing status of a document.
    
    Returns current status and results if processing is complete.
    """
    try:
        user_id = current_user.user_id
        
        # This would need to be implemented with Redis or MongoDB status tracking
        # For now, return a placeholder response
        
        # Check if document exists in MongoDB
        from src.db.mongo_db import get_mongo
        mongo_client = await get_mongo()
        
        clinical_record = await mongo_client.get_clinical_record_by_document_id(user_id, document_id)
        
        if clinical_record:
            return DocumentProcessingResponse(
                document_id=document_id,
                status="completed",
                message="Document processing completed successfully",
                processing_summary={
                    "injuries_found": len(clinical_record.get("injuries", [])),
                    "diagnoses_found": len(clinical_record.get("diagnoses", [])),
                    "procedures_found": len(clinical_record.get("procedures", [])),
                    "medications_found": len(clinical_record.get("medications", [])),
                    "processed_at": clinical_record.get("metadata", {}).get("stored_at")
                }
            )
        else:
            return DocumentProcessingResponse(
                document_id=document_id,
                status="not_found",
                message="Document not found or processing not started"
            )
        
    except Exception as e:
        logger.error(f"Failed to get processing status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing status")


@router.post("/process-sync", response_model=DocumentProcessingResponse)
async def process_document_sync(
    current_user: CurrentUser,
    file: UploadFile = File(..., description="PDF document to process"),
    document_title: Optional[str] = Form(None, description="Document title or type")
):
    """
    Synchronously process a document (for testing or small files).
    
    This runs the complete pipeline and returns results immediately.
    Use the async version for production with larger files.
    """
    try:
        user_id = current_user.user_id
        
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Check file size (10MB limit for sync processing)
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > 10 * 1024 * 1024:  # 10MB for sync
            raise HTTPException(
                status_code=400, 
                detail="File too large for synchronous processing (maximum 10MB). Use async upload instead."
            )
        
        # Generate document ID
        document_id = f"doc_{user_id}_{int(datetime.utcnow().timestamp())}_{str(uuid.uuid4())[:8]}"
        
        # Save file temporarily
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"{document_id}.pdf")
        
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_content)
        
        # Process document synchronously
        crew = MedicalDocumentCrew()
        result = crew.process_document_sync(
            user_id,
            document_id,
            temp_file_path,
            {
                "original_filename": file.filename,
                "file_size": file_size,
                "document_title": document_title
            }
        )
        
        # Clean up temp file
        try:
            os.remove(temp_file_path)
        except:
            pass
        
        # Log the result
        log_user_action(
            user_id,
            "document_processed_sync",
            {
                "document_id": document_id,
                "filename": file.filename,
                "success": result["success"],
                "processing_duration": result.get("processing_duration_seconds", 0)
            }
        )
        
        if result["success"]:
            return DocumentProcessingResponse(
                document_id=document_id,
                status="completed",
                message="Document processed successfully",
                processing_summary=result.get("summary", {})
            )
        else:
            return DocumentProcessingResponse(
                document_id=document_id,
                status="failed",
                message=f"Processing failed: {result.get('error', 'Unknown error')}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Synchronous document processing failed: {e}")
        raise HTTPException(status_code=500, detail="Document processing failed")


async def process_document_background(
    user_id: str,
    document_id: str,
    file_path: str,
    metadata: dict
):
    """
    Background task for document processing.
    
    This runs the complete CrewAI pipeline and handles cleanup.
    """
    try:
        logger.info(f"Starting background processing for document {document_id}")
        
        # Process document using CrewAI
        result = process_medical_document(user_id, document_id, file_path, metadata)
        
        # Log the result
        log_user_action(
            user_id,
            "document_processed_background",
            {
                "document_id": document_id,
                "success": result["success"],
                "processing_duration": result.get("processing_duration_seconds", 0),
                "summary": result.get("summary", {})
            }
        )
        
        if result["success"]:
            logger.info(f"Document {document_id} processed successfully in background")
        else:
            logger.error(f"Document {document_id} processing failed: {result.get('error')}")
        
        # Clean up temp file
        try:
            os.remove(file_path)
            logger.info(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temp file {file_path}: {e}")
        
    except Exception as e:
        logger.error(f"Background document processing failed for {document_id}: {e}")
        
        # Clean up temp file even if processing failed
        try:
            os.remove(file_path)
        except:
            pass


@router.get("/list")
async def list_documents(
    current_user: CurrentUser,
    limit: int = 20,
    skip: int = 0,
    document_type: Optional[str] = None
):
    """
    List processed documents for the current user.
    
    Returns basic information about all processed documents.
    """
    try:
        user_id = current_user.user_id
        
        from src.db.mongo_db import get_mongo
        mongo_client = await get_mongo()
        
        clinical_records = await mongo_client.get_clinical_records(
            user_id, limit=limit, skip=skip, document_type=document_type
        )
        
        documents = []
        for record in clinical_records:
            documents.append({
                "document_id": record["document_id"],
                "document_title": record["document_title"],
                "document_date": record["document_date"],
                "processed_at": record.get("metadata", {}).get("stored_at"),
                "summary": {
                    "injuries": len(record.get("injuries", [])),
                    "diagnoses": len(record.get("diagnoses", [])),
                    "procedures": len(record.get("procedures", [])),
                    "medications": len(record.get("medications", []))
                }
            })
        
        return {
            "documents": documents,
            "total": len(documents),
            "limit": limit,
            "skip": skip
        }
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")


@router.get("/detail/{document_id}")
async def get_document_detail(
    document_id: str,
    current_user: CurrentUser
):
    """
    Get detailed information about a processed document.
    
    Returns complete clinical data extracted from the document.
    """
    try:
        user_id = current_user.user_id
        
        from src.db.mongo_db import get_mongo
        mongo_client = await get_mongo()
        
        clinical_record = await mongo_client.get_clinical_record_by_document_id(user_id, document_id)
        
        if not clinical_record:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Remove internal MongoDB fields
        clinical_record.pop("_id", None)
        
        return clinical_record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document detail")
