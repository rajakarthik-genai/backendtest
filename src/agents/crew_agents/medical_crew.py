"""
Medical Document Processing Crew using CrewAI.
Orchestrates the complete pipeline from document reading to data storage.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from crewai import Crew, Process
from src.utils.logging import logger

from .document_reader_agent import DocumentReaderAgent
from .clinical_extractor_agent import ClinicalExtractorAgent
from .vector_embedding_agent import VectorEmbeddingAgent
from .storage_coordinator_agent import StorageCoordinatorAgent


class MedicalDocumentCrew:
    """
    CrewAI crew for comprehensive medical document processing.
    
    This crew orchestrates a complete pipeline:
    1. Document Reader: Extract text from PDF with OCR support
    2. Clinical Extractor: Extract comprehensive medical information
    3. Vector Embedding: Create embeddings for semantic search
    4. Storage Coordinator: Store data across MongoDB, Neo4j, and Redis
    """
    
    def __init__(self):
        # Initialize all agents
        self.document_reader = DocumentReaderAgent()
        self.clinical_extractor = ClinicalExtractorAgent()
        self.vector_embedder = VectorEmbeddingAgent()
        self.storage_coordinator = StorageCoordinatorAgent()
        
        # Create the crew
        self.crew = Crew(
            agents=[
                self.document_reader.agent,
                self.clinical_extractor.agent,
                self.vector_embedder.agent,
                self.storage_coordinator.agent
            ],
            process=Process.sequential,
            verbose=True,
            memory=False  # Disable memory to avoid conflicts with our custom storage
        )
    
    async def process_document(
        self,
        user_id: str,
        document_id: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a medical document through the complete pipeline.
        
        Args:
            user_id: Patient identifier for data isolation
            document_id: Unique document identifier
            file_path: Path to the PDF file
            metadata: Additional document metadata
            
        Returns:
            Complete processing results with success status and details
        """
        try:
            logger.info(f"Starting medical document processing: {document_id} for patient {user_id}")
            
            processing_start = datetime.utcnow()
            results = {
                "document_id": document_id,
                "patient_id": user_id,
                "processing_start": processing_start.isoformat(),
                "stages": {},
                "success": False,
                "error": None
            }
            
            # Stage 1: Document Reading
            logger.info("Stage 1: Document text extraction")
            try:
                text_extraction_result = self.document_reader.extract_document_text(file_path, document_id)
                results["stages"]["text_extraction"] = text_extraction_result
                
                if not text_extraction_result["success"]:
                    results["error"] = f"Text extraction failed: {text_extraction_result['error']}"
                    return results
                
                extracted_text_data = text_extraction_result
                logger.info(f"Text extraction successful: {len(extracted_text_data.get('full_text', ''))} characters")
                
            except Exception as e:
                logger.error(f"Stage 1 failed: {e}")
                results["stages"]["text_extraction"] = {"success": False, "error": str(e)}
                results["error"] = f"Text extraction stage failed: {str(e)}"
                return results
            
            # Stage 2: Clinical Data Extraction
            logger.info("Stage 2: Clinical information extraction")
            try:
                clinical_extraction_result = self.clinical_extractor.extract_clinical_data(
                    extracted_text_data, document_id
                )\n                results["stages"]["clinical_extraction"] = clinical_extraction_result
                
                if not clinical_extraction_result["success"]:
                    results["error"] = f"Clinical extraction failed: {clinical_extraction_result['error']}"
                    return results
                
                clinical_data = clinical_extraction_result["clinical_data"]
                
                # Override patient_id with the provided user_id for proper isolation
                clinical_data["patient_id"] = user_id
                clinical_data["metadata"]["original_file"] = file_path
                clinical_data["metadata"]["processing_document_id"] = document_id
                
                logger.info(f"Clinical extraction successful: {len(clinical_data.get('injuries', []))} injuries, "
                           f"{len(clinical_data.get('diagnoses', []))} diagnoses")
                
            except Exception as e:
                logger.error(f"Stage 2 failed: {e}")
                results["stages"]["clinical_extraction"] = {"success": False, "error": str(e)}
                results["error"] = f"Clinical extraction stage failed: {str(e)}"
                return results
            
            # Stage 3: Vector Embedding
            logger.info("Stage 3: Vector embedding generation")
            try:
                embedding_result = self.vector_embedder.process_embeddings(clinical_data, document_id)
                results["stages"]["vector_embedding"] = embedding_result
                
                if not embedding_result["success"]:
                    logger.warning(f"Vector embedding failed: {embedding_result['error']}")
                    # Continue processing even if embedding fails
                else:
                    logger.info(f"Embedding successful: {embedding_result.get('embeddings_stored', 0)} vectors stored")
                
            except Exception as e:
                logger.error(f"Stage 3 failed: {e}")
                results["stages"]["vector_embedding"] = {"success": False, "error": str(e)}
                # Continue processing even if embedding fails
            
            # Stage 4: Data Storage Coordination
            logger.info("Stage 4: Data storage coordination")
            try:
                storage_result = self.storage_coordinator.coordinate_storage(
                    clinical_data, document_id, user_id
                )
                results["stages"]["storage_coordination"] = storage_result
                
                if not storage_result["success"]:
                    results["error"] = f"Storage coordination failed: {storage_result.get('error', 'Unknown error')}"
                    return results
                
                logger.info(f"Storage coordination successful: {storage_result.get('successful_systems', 0)}"
                           f"/{storage_result.get('total_systems', 0)} systems")
                
            except Exception as e:
                logger.error(f"Stage 4 failed: {e}")
                results["stages"]["storage_coordination"] = {"success": False, "error": str(e)}
                results["error"] = f"Storage coordination stage failed: {str(e)}"
                return results
            
            # Calculate processing summary
            processing_end = datetime.utcnow()
            processing_duration = (processing_end - processing_start).total_seconds()
            
            results.update({
                "success": True,
                "processing_end": processing_end.isoformat(),
                "processing_duration_seconds": processing_duration,
                "summary": {
                    "text_extracted": len(extracted_text_data.get("full_text", "")),
                    "injuries_found": len(clinical_data.get("injuries", [])),
                    "diagnoses_found": len(clinical_data.get("diagnoses", [])),
                    "procedures_found": len(clinical_data.get("procedures", [])),
                    "medications_found": len(clinical_data.get("medications", [])),
                    "embeddings_created": results["stages"].get("vector_embedding", {}).get("embeddings_stored", 0),
                    "storage_systems_updated": results["stages"].get("storage_coordination", {}).get("successful_systems", 0)
                }
            })
            
            logger.info(f"Document processing completed successfully in {processing_duration:.2f} seconds")
            return results
            
        except Exception as e:
            logger.error(f"Medical document processing failed: {e}")
            return {
                "document_id": document_id,
                "patient_id": user_id,
                "success": False,
                "error": str(e),
                "processing_start": datetime.utcnow().isoformat(),
                "stages": {}
            }
    
    def process_document_sync(
        self,
        user_id: str,
        document_id: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synchronous version of document processing.
        
        Args:
            user_id: Patient identifier for data isolation
            document_id: Unique document identifier
            file_path: Path to the PDF file
            metadata: Additional document metadata
            
        Returns:
            Complete processing results with success status and details
        """
        import asyncio
        
        # Create new event loop if one doesn't exist
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.process_document(user_id, document_id, file_path, metadata)
        )
    
    def get_processing_status(self, document_id: str) -> Dict[str, Any]:
        """
        Get the processing status of a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Processing status information
        """
        # This could be implemented with Redis or MongoDB to track processing status
        # For now, return a placeholder
        return {
            "document_id": document_id,
            "status": "completed",  # This would be dynamic in a real implementation
            "message": "Document processing status tracking not implemented"
        }
    
    def validate_document(self, file_path: str) -> Dict[str, Any]:
        """
        Validate a document before processing.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Validation results
        """
        try:
            import os
            
            if not os.path.exists(file_path):
                return {
                    "valid": False,
                    "error": "File does not exist"
                }
            
            # Check file size (limit to 50MB)
            file_size = os.path.getsize(file_path)
            if file_size > 50 * 1024 * 1024:
                return {
                    "valid": False,
                    "error": "File too large (>50MB)"
                }
            
            # Check file extension
            _, ext = os.path.splitext(file_path)
            if ext.lower() not in ['.pdf']:
                return {
                    "valid": False,
                    "error": "Unsupported file format (only PDF supported)"
                }
            
            return {
                "valid": True,
                "file_size": file_size,
                "file_extension": ext
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}"
            }


# Convenience function for single document processing
def process_medical_document(
    user_id: str,
    document_id: str,
    file_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to process a single medical document.
    
    Args:
        user_id: Patient identifier for data isolation
        document_id: Unique document identifier
        file_path: Path to the PDF file
        metadata: Additional document metadata
        
    Returns:
        Complete processing results
    """
    crew = MedicalDocumentCrew()
    return crew.process_document_sync(user_id, document_id, file_path, metadata)


# Convenience function for batch processing
def process_medical_documents_batch(
    user_id: str,
    documents: List[Dict[str, str]],
    max_concurrent: int = 3
) -> List[Dict[str, Any]]:
    """
    Process multiple medical documents in batch.
    
    Args:
        user_id: Patient identifier for data isolation
        documents: List of document info dicts with 'document_id' and 'file_path'
        max_concurrent: Maximum number of concurrent processing tasks
        
    Returns:
        List of processing results for each document
    """
    import asyncio
    import concurrent.futures
    
    crew = MedicalDocumentCrew()
    results = []
    
    def process_single(doc_info):
        return crew.process_document_sync(
            user_id,
            doc_info["document_id"],
            doc_info["file_path"],
            doc_info.get("metadata")
        )
    
    # Process documents with controlled concurrency
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        future_to_doc = {
            executor.submit(process_single, doc): doc for doc in documents
        }
        
        for future in concurrent.futures.as_completed(future_to_doc):
            doc = future_to_doc[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Batch processing failed for {doc['document_id']}: {e}")
                results.append({
                    "document_id": doc["document_id"],
                    "success": False,
                    "error": str(e)
                })
    
    return results
