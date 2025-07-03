"""
File upload endpoints for medical documents and images.

Features:
- PDF and image upload support
- Background processing with status tracking
- File validation and security checks
- User isolation and metadata storage
"""

import os
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse

from src.utils.schema import UploadRequest, UploadResponse, ProcessingStatus
from src.utils.logging import logger, log_user_action
from src.db.mongo_db import get_mongo
from src.db.redis_db import get_redis
from src.agents.ingestion_agent import get_ingestion_agent
from src.auth.dependencies import AuthenticatedUserId

router = APIRouter(prefix="/upload", tags=["upload"])

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/document", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    user_id: AuthenticatedUserId,
    file: UploadFile = File(...),
    description: Optional[str] = None
):
    """
    Upload a medical document for processing.
    
    Supports PDF and image files up to 50MB.
    Processing happens in the background with status tracking.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Reset file pointer for processing
        await file.seek(0)
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Create temporary file for processing
        temp_dir = tempfile.mkdtemp(prefix="meditwin_upload_")
        temp_filename = f"{document_id}_{file.filename}"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        # Save uploaded file
        with open(temp_path, "wb") as temp_file:
            shutil.copyfileobj(file.file, temp_file)
        
        # Store document metadata in MongoDB
        mongo_client = await get_mongo()
        
        metadata = {
            "original_filename": file.filename,
            "file_size": len(contents),
            "mime_type": file.content_type,
            "description": description,
            "temp_path": temp_path
        }
        
        await mongo_client.store_document_metadata(
            user_id=user_id,
            filename=file.filename,
            file_path=temp_path,
            metadata=metadata,
            document_id=document_id
        )
        
        # Store processing status in Redis
        redis_client = get_redis()
        redis_client.store_processing_status(
            task_id=document_id,
            status="queued",
            metadata={
                "filename": file.filename,
                "file_size": len(contents),
                "user_id": user_id
            }
        )
        
        # Queue background processing
        background_tasks.add_task(
            process_document_background,
            user_id=user_id,
            document_id=document_id,  # Use same UUID for consistency
            file_path=temp_path,
            metadata=metadata
        )
        
        # Log user action
        log_user_action(
            user_id,
            "document_upload",
            {
                "document_id": document_id,
                "filename": file.filename,
                "file_size": len(contents)
            }
        )
        
        return UploadResponse(
            document_id=document_id,
            status="queued",
            message=f"Document '{file.filename}' uploaded successfully and queued for processing"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")


@router.get("/status/{document_id}")
async def get_processing_status(
    document_id: str, 
    user_id: AuthenticatedUserId
):
    """
    Get the processing status of an uploaded document.
    
    Args:
        document_id: Document identifier
        user_id: User identifier for access control
    """
    try:
        redis_client = get_redis()
        status_data = redis_client.get_processing_status(document_id)
        
        if not status_data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Verify user access
        if status_data.get("metadata", {}).get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return ProcessingStatus(
            task_id=document_id,
            status=status_data["status"],
            progress=status_data.get("progress", 0.0),
            message=status_data.get("message", ""),
            started_at=status_data.get("started_at"),
            completed_at=status_data.get("completed_at"),
            error=status_data.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processing status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")


@router.get("/documents")
async def list_user_documents(
    user_id: AuthenticatedUserId, 
    limit: int = 20
):
    """
    List all uploaded documents for a user.
    
    Args:
        user_id: User identifier
        limit: Maximum number of documents to return
    """
    try:
        mongo_client = await get_mongo()
        records = await mongo_client.get_medical_records(
            user_id=user_id,
            record_type="document",
            limit=limit
        )
        
        return {
            "user_id": user_id,
            "documents": records,
            "total": len(records)
        }
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")


@router.delete("/document/{document_id}")
async def delete_document(
    document_id: str, 
    user_id: AuthenticatedUserId
):
    """
    Delete an uploaded document and its processed data.
    
    Args:
        document_id: Document identifier
        user_id: User identifier for access control
    """
    try:
        # This would implement document deletion logic
        # Including removing files, database records, vector embeddings, etc.
        
        log_user_action(
            user_id,
            "document_delete",
            {"document_id": document_id}
        )
        
        return {
            "message": "Document deletion not fully implemented",
            "document_id": document_id
        }
        
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")


async def process_document_background(
    user_id: str,
    document_id: str,
    file_path: str,
    metadata: dict
):
    """
    Background task to process uploaded document.
    
    Args:
        user_id: User identifier
        document_id: Document identifier (UUID)
        file_path: Path to uploaded file
        metadata: Document metadata
    """
    redis_client = get_redis()
    mongo_client = await get_mongo()
    
    try:
        # Update status to processing
        redis_client.store_processing_status(
            task_id=document_id,
            status="processing",
            metadata={
                **metadata,
                "user_id": user_id,
                "started_at": datetime.utcnow().isoformat()
            }
        )
        
        # Get ingestion agent and process document
        ingestion_agent = await get_ingestion_agent()
        
        result = await ingestion_agent.process_document(
            user_id=user_id,
            document_id=document_id,
            file_path=file_path,
            metadata=metadata
        )
        
        if result["success"]:
            # Update status to completed
            redis_client.store_processing_status(
                task_id=document_id,
                status="completed",
                metadata={
                    **metadata,
                    "user_id": user_id,
                    "completed_at": datetime.utcnow().isoformat(),
                    "extracted_entities": result.get("entities", []),
                    "page_count": result.get("page_count", 0)
                }
            )
            
            # Update document status in MongoDB
            await mongo_client.update_document_processing_status(
                document_id=document_id,
                status="completed",
                metadata=result
            )
            
        else:
            # Update status to failed
            redis_client.store_processing_status(
                task_id=document_id,
                status="failed",
                metadata={
                    **metadata,
                    "user_id": user_id,
                    "error": result.get("error", "Unknown error"),
                    "completed_at": datetime.utcnow().isoformat()
                }
            )
        
        # Clean up temporary file
        try:
            os.remove(file_path)
            temp_dir = os.path.dirname(file_path)
            os.rmdir(temp_dir)
        except OSError:
            logger.warning(f"Failed to clean up temporary file: {file_path}")
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        
        # Update status to failed
        redis_client.store_processing_status(
            task_id=document_id,
            status="failed",
            metadata={
                **metadata,
                "user_id": user_id,
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            }
        )
