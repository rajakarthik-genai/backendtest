"""
Document processing endpoints - Simplified for core functionality.
"""

import os
import uuid
import tempfile
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, Field

from src.utils.logging import logger, log_user_action
from src.auth.dependencies import CurrentUser
from src.agents.crew_agents.medical_crew import process_medical_document

router = APIRouter(tags=["documents"])


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    document_id: str = Field(description="Unique document identifier")
    filename: str = Field(description="Original filename")
    file_size: int = Field(description="File size in bytes")
    status: str = Field(description="Upload status")
    processing_started: bool = Field(description="Whether processing has started")


class DocumentStatusResponse(BaseModel):
    """Response model for document status."""
    document_id: str = Field(description="Document identifier")
    filename: str = Field(description="Original filename")
    status: str = Field(description="Processing status")
    uploaded_at: str = Field(description="Upload timestamp")
    processed_at: Optional[str] = Field(None, description="Processing completion timestamp")
    file_size: int = Field(description="File size in bytes")
    extracted_text_length: Optional[int] = Field(None, description="Length of extracted text")
    medical_entities_found: Optional[int] = Field(None, description="Number of medical entities found")


class DocumentListResponse(BaseModel):
    """Response model for document listing."""
    documents: List[DocumentStatusResponse] = Field(description="List of documents")
    total_count: int = Field(description="Total number of documents")


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF document to process"),
    document_title: Optional[str] = Form(None, description="Document title or type")
):
    """
    Upload a medical document for processing.
    
    Supports PDF files with automatic text extraction and medical entity recognition.
    """
    try:
        patient_id = current_user.patient_id
        
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
        document_id = f"doc_{patient_id}_{int(datetime.utcnow().timestamp())}_{str(uuid.uuid4())[:8]}"
        
        # Save uploaded file temporarily
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"{document_id}.pdf")
        
        with open(temp_file_path, "wb") as f:
            f.write(file_content)
        
        # Store document metadata in database
        from src.db.mongo_db import get_mongo
        mongo_client = await get_mongo()
        
        document_metadata = {
                "document_id": document_id,
                    "patient_id": patient_id,
                    "filename": file.filename,
                    "file_size": file_size,
            "status": "uploaded",
            "uploaded_at": datetime.utcnow(),
            "document_title": document_title or "Medical Document",
            "file_path": temp_file_path
        }
        
        await mongo_client.store_document_metadata(patient_id, document_metadata)
        
        # Start background processing
        background_tasks.add_task(
            process_document_background,
            patient_id,
            document_id,
            temp_file_path,
            document_metadata
        )
        
        logger.info(f"Document uploaded: {document_id} for patient {patient_id[:8]}")
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=file_size,
            status="uploaded",
            processing_started=True
        )
        
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/status", response_model=DocumentListResponse)
async def get_documents_status(current_user: CurrentUser):
    """
    Get status of all uploaded documents for the patient.
    
    Returns list of documents with their processing status.
    """
    try:
        patient_id = current_user.patient_id
        
        from src.db.mongo_db import get_mongo
        mongo_client = await get_mongo()
        
        documents = await mongo_client.get_documents_status(patient_id)
        
        # Convert to response format
        document_responses = []
        for doc in documents:
            document_responses.append(DocumentStatusResponse(
                document_id=doc.get("document_id"),
                filename=doc.get("filename"),
                status=doc.get("status", "unknown"),
                uploaded_at=doc.get("uploaded_at", "").isoformat() if doc.get("uploaded_at") else "",
                processed_at=doc.get("processed_at", "").isoformat() if doc.get("processed_at") else None,
                file_size=doc.get("file_size", 0),
                extracted_text_length=doc.get("extracted_text_length"),
                medical_entities_found=doc.get("medical_entities_found")
            ))
        
        return DocumentListResponse(
            documents=document_responses,
            total_count=len(document_responses)
        )
        
    except Exception as e:
        logger.error(f"Failed to get documents status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")


@router.get("/status/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str, current_user: CurrentUser):
    """
    Get status of a specific document.
    """
    try:
        patient_id = current_user.patient_id
        
        from src.db.mongo_db import get_mongo
        mongo_client = await get_mongo()
        
        document = await mongo_client.get_document_status(patient_id, document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentStatusResponse(
            document_id=document.get("document_id"),
            filename=document.get("filename"),
            status=document.get("status", "unknown"),
            uploaded_at=document.get("uploaded_at", "").isoformat() if document.get("uploaded_at") else "",
            processed_at=document.get("processed_at", "").isoformat() if document.get("processed_at") else None,
            file_size=document.get("file_size", 0),
            extracted_text_length=document.get("extracted_text_length"),
            medical_entities_found=document.get("medical_entities_found")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")


async def process_document_background(
    patient_id: str,
    document_id: str,
    file_path: str,
    metadata: dict
):
    """Background task to process uploaded document."""
    try:
        from src.db.mongo_db import get_mongo
        mongo_client = await get_mongo()
        
        # Update status to processing
        await mongo_client.update_document_status(patient_id, document_id, "processing")
        
        # Process document using medical crew
        result = await process_medical_document(
            patient_id=patient_id,
            document_id=document_id,
            file_path=file_path,
            document_title=metadata.get("document_title", "Medical Document")
        )
        
        # Update status to completed
        await mongo_client.update_document_status(
            patient_id,
            document_id, 
            "completed",
            {
                "processed_at": datetime.utcnow(),
                "extracted_text_length": result.get("text_length", 0),
                "medical_entities_found": result.get("entities_count", 0),
                "processing_result": result
            }
        )
        
        logger.info(f"Document processing completed: {document_id}")
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        # Update status to failed
        try:
            await mongo_client.update_document_status(patient_id, document_id, "failed", {"error": str(e)})
        except:
            pass


@router.get("/health")
async def get_documents_health_check():
    """Health check for document processing service."""
    return {
            "status": "healthy",
        "service": "document_processing",
        "version": "1.0.0",
        "features": [
            "PDF upload and processing",
            "Medical entity extraction",
            "Background processing",
            "Status tracking"
        ]
        }
