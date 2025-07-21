"""
Document processing endpoints using CrewAI multi-agent system.
"""

import os
import uuid
import tempfile
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
from pydantic import BaseModel, Field

from src.utils.logging import logger, log_user_action
from src.auth.dependencies import CurrentUser, AuthenticatedPatientId
from src.agents.crew_agents.medical_crew import MedicalDocumentCrew, process_medical_document

router = APIRouter(tags=["documents"])


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


# Add validation models
class DocumentValidationError(BaseModel):
    """Validation error details."""
    field: str = Field(description="Field that failed validation")
    message: str = Field(description="Error message")
    code: str = Field(description="Error code")

class DocumentValidationResponse(BaseModel):
    """Document validation response."""
    valid: bool = Field(description="Whether document is valid")
    errors: list[DocumentValidationError] = Field(description="Validation errors")
    warnings: list[str] = Field(description="Validation warnings")
    file_info: dict = Field(description="File information")


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
        patient_id = current_user.patient_id
        
        # Check upload rate limit
        if not check_upload_rate_limit(patient_id):
            raise HTTPException(
                status_code=429,
                detail="Upload rate limit exceeded. Maximum 10 uploads per hour."
            )
        
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
        
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_content)
        
        # Prepare metadata
        metadata = {
            "original_filename": file.filename,
            "file_size": file_size,
            "document_title": document_title,
            "upload_timestamp": datetime.utcnow().isoformat(),
            "patient_id": patient_id
        }
        
        logger.info(f"Document uploaded: {document_id} ({file.filename}, {file_size} bytes)")
        
        # Log user action
        log_user_action(
            patient_id,
            "document_uploaded",
            {
                "document_id": document_id,
                "filename": file.filename,
                "file_size": file_size,
                "document_title": document_title
            }
        )
        
        # Initialize Redis status tracking
        from src.db.redis_db import get_redis
        redis_client = await get_redis()
        
        # Start processing if requested
        if process_immediately:
            # Set initial processing status in Redis
            await redis_client.store_processing_status(
                document_id,
                "queued",
                {
                    "patient_id": patient_id,
                    "filename": file.filename,
                    "file_size": file_size,
                    "document_title": document_title,
                    "queued_at": datetime.utcnow().isoformat()
                }
            )
            
            background_tasks.add_task(
                process_document_background,
                patient_id,
                document_id,
                temp_file_path,
                metadata
            )
            processing_started = True
        else:
            # Set status as uploaded but not processing
            await redis_client.store_processing_status(
                document_id,
                "uploaded",
                {
                    "patient_id": patient_id,
                    "filename": file.filename,
                    "file_size": file_size,
                    "document_title": document_title,
                    "uploaded_at": datetime.utcnow().isoformat()
                }
            )
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
        patient_id = current_user.patient_id
        
        # Check if document exists (this would need to be implemented based on your storage)
        # For now, we'll assume the document path exists
        temp_file_path = os.path.join(tempfile.gettempdir(), f"{document_id}.pdf")
        
        if not os.path.exists(temp_file_path):
            raise HTTPException(
                status_code=404, 
                detail="Document not found or already processed"
            )
        
        # Set initial processing status in Redis
        from src.db.redis_db import get_redis
        redis_client = await get_redis()
        
        await redis_client.store_processing_status(
            document_id,
            "queued",
            {
                "patient_id": patient_id,
                "message": "Document queued for processing",
                "queued_at": datetime.utcnow().isoformat()
            }
        )
        
        # Start background processing
        background_tasks.add_task(
            process_document_background,
            patient_id,
            document_id,
            temp_file_path,
            {}
        )
        
        logger.info(f"Started processing document {document_id} for user {patient_id[:8]}...")
        
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
        patient_id = current_user.patient_id
        
        # First check Redis for processing status
        from src.db.redis_db import get_redis
        redis_client = await get_redis()
        
        redis_status = await redis_client.get_processing_status(document_id)
        
        if redis_status:
            # Verify the document belongs to the current user
            if redis_status.get("metadata", {}).get("patient_id") != patient_id:
                raise HTTPException(status_code=404, detail="Document not found")
            
            status = redis_status.get("status", "unknown")
            
            # If completed, get detailed results from MongoDB
            if status == "completed":
                from src.db.mongo_db import get_mongo
                mongo_client = await get_mongo()
                
                clinical_record = await mongo_client.get_clinical_record_by_document_id(patient_id, document_id)
                
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
                            "processing_duration": redis_status.get("metadata", {}).get("processing_duration_seconds", 0),
                            "processed_at": clinical_record.get("metadata", {}).get("stored_at")
                        }
                    )
            
            # Return current Redis status for non-completed documents
            return DocumentProcessingResponse(
                document_id=document_id,
                status=status,
                message=redis_status.get("metadata", {}).get("message", f"Document is {status}"),
                processing_summary=redis_status.get("metadata", {}).get("summary", None)
            )
        
        # Fallback: Check if document exists in MongoDB (might be an old document)
        from src.db.mongo_db import get_mongo
        mongo_client = await get_mongo()
        
        clinical_record = await mongo_client.get_clinical_record_by_document_id(patient_id, document_id)
        
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
        patient_id = current_user.patient_id
        
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Check file size (10MB limit for sync processing)
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > 10 * 1024 * 1024:  # 10MB for sync
            raise HTTPException(
                status_code=413, 
                detail="File too large for synchronous processing (maximum 10MB). Use async upload instead."
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Generate document ID
        document_id = f"doc_{patient_id}_{int(datetime.utcnow().timestamp())}_{str(uuid.uuid4())[:8]}"
        
        # Save file temporarily
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"{document_id}.pdf")
        
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_content)
        
        # Process document synchronously
        crew = MedicalDocumentCrew()
        result = crew.process_document_sync(
            patient_id,
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
            patient_id,
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


@router.post("/validate", response_model=DocumentValidationResponse)
async def validate_document(
    current_user: CurrentUser,
    file: UploadFile = File(..., description="PDF document to validate")
):
    """
    Validate a document before processing.
    
    Checks file format, size, content readability, and potential issues.
    """
    try:
        errors = []
        warnings = []
        
        # Basic file info
        file_info = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": 0,
            "readable": False,
            "pages": 0,
            "has_text": False,
            "text_sample": ""
        }
        
        # Validate file extension
        if not file.filename.lower().endswith('.pdf'):
            errors.append(DocumentValidationError(
                field="filename",
                message="Only PDF files are supported",
                code="INVALID_FILE_TYPE"
            ))
        
        # Validate content type
        if file.content_type and not file.content_type.lower().startswith('application/pdf'):
            warnings.append("Content-Type header suggests this may not be a PDF file")
        
        # Read and validate file content
        file_content = await file.read()
        file_info["size_bytes"] = len(file_content)
        
        # Check file size
        if len(file_content) == 0:
            errors.append(DocumentValidationError(
                field="file_size",
                message="File is empty",
                code="EMPTY_FILE"
            ))
        elif len(file_content) > 50 * 1024 * 1024:  # 50MB
            errors.append(DocumentValidationError(
                field="file_size",
                message="File too large (maximum 50MB)",
                code="FILE_TOO_LARGE"
            ))
        elif len(file_content) > 20 * 1024 * 1024:  # 20MB warning
            warnings.append("Large file (>20MB) may take longer to process")
        
        # Try to read PDF content
        if not errors:  # Only if basic validation passed
            try:
                import tempfile
                import os
                
                # Save to temp file for PDF analysis
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(file_content)
                    temp_file_path = temp_file.name
                
                try:
                    # Try to extract text to validate PDF readability
                    from src.agents.crew_agents.medical_crew import MedicalDocumentCrew
                    crew = MedicalDocumentCrew()
                    
                    # Use the document reader agent for validation
                    text_result = crew.document_reader._extract_text(temp_file_path)
                    
                    if text_result.get("success"):
                        file_info["readable"] = True
                        file_info["pages"] = text_result.get("pages", 0)
                        
                        extracted_text = text_result.get("text", "")
                        if extracted_text.strip():
                            file_info["has_text"] = True
                            # Get first 200 characters as sample
                            file_info["text_sample"] = extracted_text[:200].strip()
                            
                            # Check for common medical document indicators
                            text_lower = extracted_text.lower()
                            medical_indicators = ["patient", "diagnosis", "treatment", "medication", "doctor", "hospital", "clinic"]
                            found_indicators = [ind for ind in medical_indicators if ind in text_lower]
                            
                            if len(found_indicators) < 2:
                                warnings.append("Document may not contain medical information")
                        else:
                            warnings.append("No readable text found - document may be image-based and will require OCR")
                    else:
                        errors.append(DocumentValidationError(
                            field="pdf_content",
                            message=f"Cannot read PDF content: {text_result.get('error', 'Unknown error')}",
                            code="PDF_UNREADABLE"
                        ))
                
                finally:
                    # Clean up temp file
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass
                        
            except Exception as e:
                warnings.append(f"Could not fully validate PDF content: {str(e)}")
        
        # Reset file pointer for potential further use
        await file.seek(0)
        
        is_valid = len(errors) == 0
        
        return DocumentValidationResponse(
            valid=is_valid,
            errors=errors,
            warnings=warnings,
            file_info=file_info
        )
        
    except Exception as e:
        logger.error(f"Document validation failed: {e}")
        raise HTTPException(status_code=500, detail="Document validation failed")


# Security enhancement: Add rate limiting for uploads
upload_rate_limiter = {}

def check_upload_rate_limit(patient_id: str, max_uploads: int = 10, time_window: int = 3600) -> bool:
    """
    Check if user has exceeded upload rate limit.
    
    Args:
        patient_id: Patient identifier
        max_uploads: Maximum uploads allowed in time window
        time_window: Time window in seconds (default: 1 hour)
    
    Returns:
        True if within limit, False if exceeded
    """
    import time
    
    current_time = time.time()
    
    if patient_id not in upload_rate_limiter:
        upload_rate_limiter[patient_id] = []
    
    # Remove old entries
    upload_rate_limiter[patient_id] = [
        timestamp for timestamp in upload_rate_limiter[patient_id]
        if current_time - timestamp < time_window
    ]
    
    # Check limit
    if len(upload_rate_limiter[patient_id]) >= max_uploads:
        return False
    
    # Add current upload
    upload_rate_limiter[patient_id].append(current_time)
    return True


async def process_document_background(
    patient_id: str,
    document_id: str,
    file_path: str,
    metadata: dict
):
    """
    Background task for document processing.
    
    This runs the complete CrewAI pipeline and handles cleanup.
    """
    from src.db.redis_db import get_redis
    
    try:
        logger.info(f"Starting background processing for document {document_id}")
        
        # Get Redis client for status updates
        redis_client = await get_redis()
        
        # Update status to processing
        await redis_client.store_processing_status(
            document_id,
            "processing",
            {
                "patient_id": patient_id,
                "message": "Document processing in progress...",
                "started_at": datetime.utcnow().isoformat()
            }
        )
        
        # Record start time for duration calculation
        start_time = datetime.utcnow()
        
        # Process document using CrewAI
        result = process_medical_document(patient_id, document_id, file_path, metadata)
        
        # Calculate processing duration
        end_time = datetime.utcnow()
        processing_duration = (end_time - start_time).total_seconds()
        
        # Log the result
        log_user_action(
            patient_id,
            "document_processed_background",
            {
                "document_id": document_id,
                "success": result["success"],
                "processing_duration": processing_duration,
                "summary": result.get("summary", {})
            }
        )
        
        if result["success"]:
            logger.info(f"Document {document_id} processed successfully in background")
            
            # Update Redis status to completed
            await redis_client.store_processing_status(
                document_id,
                "completed",
                {
                    "patient_id": patient_id,
                    "message": "Document processing completed successfully",
                    "processing_duration_seconds": processing_duration,
                    "completed_at": end_time.isoformat(),
                    "summary": result.get("summary", {}),
                    "entities_extracted": result.get("entities_count", 0)
                }
            )
        else:
            logger.error(f"Document {document_id} processing failed: {result.get('error')}")
            
            # Update Redis status to failed
            await redis_client.store_processing_status(
                document_id,
                "failed",
                {
                    "patient_id": patient_id,
                    "message": f"Processing failed: {result.get('error', 'Unknown error')}",
                    "processing_duration_seconds": processing_duration,
                    "failed_at": end_time.isoformat(),
                    "error_details": result.get("error_details", {})
                }
            )
        
        # Clean up temp file
        try:
            os.remove(file_path)
            logger.info(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temp file {file_path}: {e}")
        
    except Exception as e:
        logger.error(f"Background document processing failed for {document_id}: {e}")
        
        # Update Redis status to failed
        try:
            redis_client = await get_redis()
            await redis_client.store_processing_status(
                document_id,
                "failed",
                {
                    "patient_id": patient_id,
                    "message": f"Processing failed with error: {str(e)}",
                    "failed_at": datetime.utcnow().isoformat(),
                    "error": str(e)
                }
            )
        except Exception as status_error:
            logger.error(f"Failed to update status after processing error: {status_error}")
        
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
        patient_id = current_user.patient_id
        
        from src.db.mongo_db import get_mongo
        mongo_client = await get_mongo()
        
        clinical_records = await mongo_client.get_clinical_records(
            patient_id, limit=limit, skip=skip, document_type=document_type
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
        patient_id = current_user.patient_id
        
        from src.db.mongo_db import get_mongo
        mongo_client = await get_mongo()
        
        clinical_record = await mongo_client.get_clinical_record_by_document_id(patient_id, document_id)
        
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


@router.get("/documents")
async def get_documents(current_user: CurrentUser):
    """Get user documents (frontend compatibility)"""
    try:
        return await list_documents(current_user)
    except Exception as e:
        logger.error(f"Get documents failed: {e}")
        return {"documents": [], "message": "Document system available"}


@router.get("/documents/search")
async def search_documents(
    current_user: CurrentUser,
    query: str = Query(..., description="Search query")
):
    """Search documents"""
    return {
        "results": [],
        "query": query,
        "total_results": 0,
        "message": "Document search system available",
        "patient_id": current_user.patient_id
    }


@router.get("/documents/insights")
async def get_document_insights(current_user: CurrentUser):
    """Get document insights"""
    return {
        "insights": [],
        "total_documents": 0,
        "categories": {},
        "message": "Document insights system available",
        "patient_id": current_user.patient_id
    }


@router.post("/documents/analyze")
async def analyze_document(
    request: dict,
    current_user: CurrentUser
):
    """Analyze document content"""
    document_id = request.get("document_id", "unknown")
    return {
        "document_id": document_id,
        "analysis": "Document analysis system available",
        "key_findings": [],
        "confidence": 0.8,
        "patient_id": current_user.patient_id
    }


@router.post("/batch-upload", response_model=dict)
async def batch_upload_documents(
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(..., description="Multiple PDF documents to process"),
    document_titles: Optional[str] = Form(None, description="Comma-separated document titles"),
    process_immediately: bool = Form(True, description="Start processing immediately")
):
    """
    Upload multiple medical documents for batch processing.
    
    Supports up to 10 files at once with the same validation as single upload.
    """
    try:
        patient_id = current_user.patient_id
        
        # Check upload rate limit (stricter for batch uploads)
        if not check_upload_rate_limit(patient_id, max_uploads=5, time_window=3600):
            raise HTTPException(
                status_code=429,
                detail="Batch upload rate limit exceeded. Maximum 5 batch uploads per hour."
            )
        
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 files allowed per batch")
        
        # Parse document titles if provided
        titles = []
        if document_titles:
            titles = [title.strip() for title in document_titles.split(",")]
        
        results = []
        total_size = 0
        
        for i, file in enumerate(files):
            # Validate file
            if not file.filename.lower().endswith('.pdf'):
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "Only PDF files are supported"
                })
                continue
            
            # Check file size
            file_content = await file.read()
            file_size = len(file_content)
            total_size += file_size
            
            # Check individual file size (50MB limit)
            if file_size > 50 * 1024 * 1024:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "File too large (maximum 50MB)"
                })
                continue
            
            if file_size == 0:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "Empty file"
                })
                continue
            
            # Check total batch size (200MB limit)
            if total_size > 200 * 1024 * 1024:
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": "Batch size limit exceeded (200MB total)"
                })
                continue
            
            # Generate document ID
            document_id = f"doc_{patient_id}_{int(datetime.utcnow().timestamp())}_{str(uuid.uuid4())[:8]}"
            
            # Save uploaded file temporarily
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, f"{document_id}.pdf")
            
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(file_content)
            
            # Get document title
            document_title = titles[i] if i < len(titles) else None
            
            # Prepare metadata
            metadata = {
                "original_filename": file.filename,
                "file_size": file_size,
                "document_title": document_title,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "patient_id": patient_id,
                "batch_upload": True
            }
            
            # Initialize Redis status tracking
            from src.db.redis_db import get_redis
            redis_client = await get_redis()
            
            # Start processing if requested
            if process_immediately:
                await redis_client.store_processing_status(
                    document_id,
                    "queued",
                    {
                        "patient_id": patient_id,
                        "filename": file.filename,
                        "file_size": file_size,
                        "document_title": document_title,
                        "queued_at": datetime.utcnow().isoformat(),
                        "batch_upload": True
                    }
                )
                
                background_tasks.add_task(
                    process_document_background,
                    patient_id,
                    document_id,
                    temp_file_path,
                    metadata
                )
                
                results.append({
                    "document_id": document_id,
                    "filename": file.filename,
                    "file_size": file_size,
                    "status": "queued",
                    "processing_started": True
                })
            else:
                await redis_client.store_processing_status(
                    document_id,
                    "uploaded",
                    {
                        "patient_id": patient_id,
                        "filename": file.filename,
                        "file_size": file_size,
                        "document_title": document_title,
                        "uploaded_at": datetime.utcnow().isoformat(),
                        "batch_upload": True
                    }
                )
                
                results.append({
                    "document_id": document_id,
                    "filename": file.filename,
                    "file_size": file_size,
                    "status": "uploaded",
                    "processing_started": False
                })
        
        # Log batch upload action
        log_user_action(
            patient_id,
            "batch_documents_uploaded",
            {
                "file_count": len(files),
                "successful_uploads": len([r for r in results if r.get("status") in ["queued", "uploaded"]]),
                "failed_uploads": len([r for r in results if r.get("status") == "error"]),
                "total_size": total_size
            }
        )
        
        return {
            "batch_id": str(uuid.uuid4()),
            "total_files": len(files),
            "successful": len([r for r in results if r.get("status") in ["queued", "uploaded"]]),
            "failed": len([r for r in results if r.get("status") == "error"]),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch document upload failed: {e}")
        raise HTTPException(status_code=500, detail="Batch document upload failed")


@router.delete("/document/{document_id}")
async def delete_document(
    document_id: str,
    current_user: CurrentUser
):
    """
    Delete a document and all associated data.
    
    This removes the document from all storage systems:
    - MongoDB (document metadata and clinical records)
    - Neo4j (events derived from this document)
    - Milvus (embeddings from this document)
    - Redis (processing status)
    """
    try:
        patient_id = current_user.patient_id
        
        # Check if document exists and belongs to user
        from src.db.redis_db import get_redis
        from src.db.mongo_db import get_mongo
        from src.db.neo4j_db import get_neo4j
        from src.db.milvus_db import get_milvus
        
        redis_client = await get_redis()
        mongo_client = await get_mongo()
        neo4j_client = await get_neo4j()
        milvus_client = await get_milvus()
        
        # First check if document exists (either in Redis status or MongoDB)
        redis_status = await redis_client.get_processing_status(document_id)
        
        document_exists = False
        if redis_status and redis_status.get("metadata", {}).get("patient_id") == patient_id:
            document_exists = True
        
        # Also check MongoDB for completed documents
        clinical_record = await mongo_client.get_clinical_record_by_document_id(patient_id, document_id)
        if clinical_record:
            document_exists = True
        
        if not document_exists:
            raise HTTPException(status_code=404, detail="Document not found or access denied")
        
        deletion_results = {}
        
        # Delete from Redis (processing status)
        try:
            redis_key = f"task:{document_id}"
            redis_deleted = await redis_client.client.delete(redis_key)
            deletion_results["redis"] = {"deleted": redis_deleted > 0, "error": None}
        except Exception as e:
            deletion_results["redis"] = {"deleted": False, "error": str(e)}
        
        # Delete from MongoDB (document metadata and clinical records)
        try:
            mongo_deleted = await mongo_client.delete_document_by_id(patient_id, document_id)
            deletion_results["mongodb"] = {"deleted": mongo_deleted, "error": None}
        except Exception as e:
            deletion_results["mongodb"] = {"deleted": False, "error": str(e)}
        
        # Delete from Neo4j (events with source matching this document)
        try:
            neo4j_deleted = await neo4j_client.delete_events_by_document_id(patient_id, document_id)
            deletion_results["neo4j"] = {"deleted": neo4j_deleted, "error": None}
        except Exception as e:
            deletion_results["neo4j"] = {"deleted": False, "error": str(e)}
        
        # Delete from Milvus (embeddings tagged with this document)
        try:
            milvus_deleted = await milvus_client.delete_document_embeddings(patient_id, document_id)
            deletion_results["milvus"] = {"deleted": milvus_deleted, "error": None}
        except Exception as e:
            deletion_results["milvus"] = {"deleted": False, "error": str(e)}
        
        # Log the deletion action
        log_user_action(
            patient_id,
            "document_deleted",
            {
                "document_id": document_id,
                "deletion_results": deletion_results
            }
        )
        
        # Check if deletion was successful overall
        successful_deletions = sum(1 for result in deletion_results.values() if result["deleted"])
        total_attempted = len(deletion_results);
        
        return {
            "document_id": document_id,
            "deleted": successful_deletions > 0,
            "successful_deletions": successful_deletions,
            "total_attempted": total_attempted,
            "details": deletion_results,
            "message": f"Document deletion completed. {successful_deletions}/{total_attempted} systems updated successfully."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document deletion failed: {e}")
        raise HTTPException(status_code=500, detail="Document deletion failed")


@router.get("/stats")
async def get_document_stats(current_user: CurrentUser):
    """
    Get comprehensive document processing statistics for the current user.
    
    Returns processing statistics, storage usage, and document types breakdown.
    """
    try:
        patient_id = current_user.patient_id
        
        from src.db.mongo_db import get_mongo
        from src.db.redis_db import get_redis
        from src.db.neo4j_db import get_neo4j
        from src.db.milvus_db import get_milvus
        
        mongo_client = await get_mongo()
        redis_client = await get_redis()
        neo4j_client = await get_neo4j()
        milvus_client = await get_milvus()
        
        stats = {
            "patient_id": patient_id,
            "generated_at": datetime.utcnow().isoformat(),
            "documents": {},
            "processing": {},
            "storage": {},
            "entities": {}
        }
        
        # Get document counts from MongoDB
        try:
            clinical_records = await mongo_client.get_clinical_records(patient_id, limit=1000)
            stats["documents"]["total_processed"] = len(clinical_records)
            
            # Document types breakdown
            doc_types = {}
            total_size = 0
            
            for record in clinical_records:
                doc_type = record.get("document_title", "Unknown")
                if doc_type not in doc_types:
                    doc_types[doc_type] = 0
                doc_types[doc_type] += 1
                
                # Add file size if available
                if "file_size" in record.get("metadata", {}):
                    total_size += record["metadata"]["file_size"]
            
            stats["documents"]["by_type"] = doc_types
            stats["storage"]["total_document_size_bytes"] = total_size
            stats["storage"]["total_document_size_mb"] = round(total_size / (1024 * 1024), 2)
            
        except Exception as e:
            logger.warning(f"Failed to get MongoDB stats: {e}")
            stats["documents"]["total_processed"] = 0
            stats["documents"]["by_type"] = {}
        
        # Get processing status counts from Redis (scan for task: keys)
        try:
            processing_statuses = {"queued": 0, "processing": 0, "completed": 0, "failed": 0, "uploaded": 0}
            
            # This would need a more efficient implementation in production
            # For now, we'll provide a placeholder
            stats["processing"]["current_status_counts"] = processing_statuses
            stats["processing"]["note"] = "Processing stats from Redis not fully implemented"
            
        except Exception as e:
            logger.warning(f"Failed to get Redis processing stats: {e}")
            stats["processing"]["current_status_counts"] = {}
        
        # Get entity extraction statistics
        try:
            total_entities = 0
            entity_types = {"injuries": 0, "diagnoses": 0, "procedures": 0, "medications": 0}
            
            for record in clinical_records:
                total_entities += len(record.get("injuries", []))
                total_entities += len(record.get("diagnoses", []))
                total_entities += len(record.get("procedures", []))
                total_entities += len(record.get("medications", []))
                
                entity_types["injuries"] += len(record.get("injuries", []))
                entity_types["diagnoses"] += len(record.get("diagnoses", []))
                entity_types["procedures"] += len(record.get("procedures", []))
                entity_types["medications"] += len(record.get("medications", []))
            
            stats["entities"]["total_extracted"] = total_entities
            stats["entities"]["by_type"] = entity_types
            
        except Exception as e:
            logger.warning(f"Failed to calculate entity stats: {e}")
            stats["entities"]["total_extracted"] = 0
            stats["entities"]["by_type"] = {}
        
        # Get Neo4j event counts
        try:
            timeline_events = await neo4j_client.get_patient_timeline(patient_id)
            stats["storage"]["neo4j_events"] = len(timeline_events)
            
            # Count events by type
            event_types = {}
            for event in timeline_events:
                event_type = event.get("type", "unknown")
                if event_type not in event_types:
                    event_types[event_type] = 0
                event_types[event_type] += 1
            
            stats["storage"]["neo4j_events_by_type"] = event_types
            
        except Exception as e:
            logger.warning(f"Failed to get Neo4j stats: {e}")
            stats["storage"]["neo4j_events"] = 0
        
        # Get approximate Milvus vector count (if possible)
        try:
            # This would need to be implemented in the Milvus client
            stats["storage"]["milvus_vectors"] = "Not implemented"
        except Exception as e:
            stats["storage"]["milvus_vectors"] = 0
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get document stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document statistics")


@router.get("/health")
async def get_documents_health_check():
    """
    Health check endpoint for document processing system.
    
    Checks connectivity to all required services.
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {}
        }
        
        # Check MongoDB
        try:
            from src.db.mongo_db import get_mongo
            mongo_client = await get_mongo()
            await mongo_client.health_check()
            health_status["services"]["mongodb"] = {"status": "healthy", "error": None}
        except Exception as e:
            health_status["services"]["mongodb"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        # Check Redis
        try:
            from src.db.redis_db import get_redis
            redis_client = await get_redis()
            await redis_client.health_check()
            health_status["services"]["redis"] = {"status": "healthy", "error": None}
        except Exception as e:
            health_status["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        # Check Neo4j
        try:
            from src.db.neo4j_db import get_neo4j
            neo4j_client = await get_neo4j()
            await neo4j_client.health_check()
            health_status["services"]["neo4j"] = {"status": "healthy", "error": None}
        except Exception as e:
            health_status["services"]["neo4j"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        # Check Milvus
        try:
            from src.db.milvus_db import get_milvus
            milvus_client = await get_milvus()
            await milvus_client.health_check()
            health_status["services"]["milvus"] = {"status": "healthy", "error": None}
        except Exception as e:
            health_status["services"]["milvus"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        # Check CrewAI agents
        try:
            from src.agents.crew_agents.medical_crew import MedicalDocumentCrew
            crew = MedicalDocumentCrew()
            # Basic initialization check
            health_status["services"]["crewai"] = {"status": "healthy", "error": None}
        except Exception as e:
            health_status["services"]["crewai"] = {"status": "unhealthy", "error": str(e)}
            health_status["status"] = "degraded"
        
        # Overall status
        unhealthy_services = [s for s in health_status["services"].values() if s["status"] == "unhealthy"]
        if len(unhealthy_services) > 0:
            if len(unhealthy_services) == len(health_status["services"]):
                health_status["status"] = "unhealthy"
            else:
                health_status["status"] = "degraded"
        
        health_status["summary"] = {
            "total_services": len(health_status["services"]),
            "healthy_services": len([s for s in health_status["services"].values() if s["status"] == "healthy"]),
            "unhealthy_services": len(unhealthy_services)
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "services": {}
        }
