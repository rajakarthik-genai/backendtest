"""
Vector Embedding Agent for CrewAI pipeline.
Handles text chunking, embedding generation, and Milvus storage.
"""

import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime

from crewai import Agent, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.utils.logging import logger
from src.db.milvus_db import get_milvus


class TextChunk(BaseModel):
    """Model for text chunks."""
    text: str = Field(description="Chunk text content")
    chunk_id: str = Field(description="Unique chunk identifier")
    metadata: Dict[str, Any] = Field(description="Chunk metadata")


class EmbeddingResult(BaseModel):
    """Model for embedding results."""
    chunk_id: str = Field(description="Chunk identifier")
    vector: List[float] = Field(description="Embedding vector")
    metadata: Dict[str, Any] = Field(description="Associated metadata")


class TextChunkingTool(BaseTool):
    """Tool for intelligent text chunking."""
    
    name: str = "text_chunker"
    description: str = "Split text into meaningful chunks for embedding"
    
    def _run(self, clinical_data: Dict[str, Any], max_chunk_size: int = 300) -> Dict[str, Any]:
        """Chunk clinical text into meaningful segments."""
        try:
            logger.info("Starting text chunking for embedding")
            
            chunks = []
            chunk_counter = 0
            
            # Extract metadata for all chunks
            base_metadata = {
                "patient_id": clinical_data.get("patient_id", "Not Available"),
                "document_id": clinical_data.get("metadata", {}).get("source_file", "Unknown"),
                "document_date": clinical_data.get("document_date", "Not Available"),
                "document_title": clinical_data.get("document_title", "Not Available"),
                "extracted_at": datetime.utcnow().isoformat()
            }
            
            # Chunk SOAP note sections
            soap_sections = [
                ("subjective", clinical_data.get("subjective_note_text", "")),
                ("objective", clinical_data.get("objective_note_text", "")),
                ("assessment", clinical_data.get("assessment_note_text", "")),
                ("plan", clinical_data.get("plan_note_text", ""))
            ]
            
            for section_name, section_text in soap_sections:
                if section_text and section_text != "Not Available":
                    section_chunks = self._chunk_text(section_text, max_chunk_size)
                    
                    for i, chunk_text in enumerate(section_chunks):
                        chunk_id = f"{base_metadata['patient_id']}_{section_name}_{chunk_counter}"
                        chunk_metadata = {
                            **base_metadata,
                            "section": section_name,
                            "chunk_index": i,
                            "chunk_type": "soap_section",
                            "text_length": len(chunk_text)
                        }
                        
                        chunks.append({
                            "text": chunk_text,
                            "chunk_id": chunk_id,
                            "metadata": chunk_metadata
                        })
                        chunk_counter += 1
            
            # Chunk other narrative sections
            narrative_sections = [
                ("feedback", clinical_data.get("feedback", "")),
                ("recovery_progress", clinical_data.get("recovery_progress", "")),
                ("patient_history", clinical_data.get("patient_history", ""))
            ]
            
            for section_name, section_text in narrative_sections:
                if section_text and section_text != "Not Available":
                    section_chunks = self._chunk_text(section_text, max_chunk_size)
                    
                    for i, chunk_text in enumerate(section_chunks):
                        chunk_id = f"{base_metadata['patient_id']}_{section_name}_{chunk_counter}"
                        chunk_metadata = {
                            **base_metadata,
                            "section": section_name,
                            "chunk_index": i,
                            "chunk_type": "narrative",
                            "text_length": len(chunk_text)
                        }
                        
                        chunks.append({
                            "text": chunk_text,
                            "chunk_id": chunk_id,
                            "metadata": chunk_metadata
                        })
                        chunk_counter += 1
            
            # Create structured data summaries for embedding
            structured_summaries = self._create_structured_summaries(clinical_data)
            
            for summary_type, summary_text in structured_summaries.items():
                if summary_text:
                    chunk_id = f"{base_metadata['patient_id']}_{summary_type}_{chunk_counter}"
                    chunk_metadata = {
                        **base_metadata,
                        "section": summary_type,
                        "chunk_index": 0,
                        "chunk_type": "structured_summary",
                        "text_length": len(summary_text)
                    }
                    
                    chunks.append({
                        "text": summary_text,
                        "chunk_id": chunk_id,
                        "metadata": chunk_metadata
                    })
                    chunk_counter += 1
            
            logger.info(f"Created {len(chunks)} text chunks for embedding")
            
            return {
                "success": True,
                "chunks": chunks,
                "total_chunks": len(chunks),
                "metadata": base_metadata
            }
            
        except Exception as e:
            logger.error(f"Text chunking failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "chunks": []
            }
    
    def _chunk_text(self, text: str, max_size: int) -> List[str]:
        """Split text into chunks with overlap."""
        if len(text) <= max_size:
            return [text]
        
        chunks = []
        overlap = 50  # Character overlap between chunks
        
        # Split by sentences first
        sentences = self._split_sentences(text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    
                    # Start new chunk with overlap
                    overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                    current_chunk = overlap_text + sentence + " "
                else:
                    # Single sentence too long, split by words
                    current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _create_structured_summaries(self, clinical_data: Dict[str, Any]) -> Dict[str, str]:
        """Create summaries of structured data for embedding."""
        summaries = {}
        
        # Injuries summary
        injuries = clinical_data.get("injuries", [])
        if injuries:
            injury_texts = []
            for injury in injuries:
                injury_text = f"Injury: {injury.get('description', 'Unknown')} affecting {injury.get('body_part', 'unknown body part')} with {injury.get('severity', 'unknown')} severity"
                if injury.get('date') != "Not Available":
                    injury_text += f" on {injury.get('date')}"
                injury_texts.append(injury_text)
            summaries["injuries_summary"] = ". ".join(injury_texts)
        
        # Diagnoses summary
        diagnoses = clinical_data.get("diagnoses", [])
        if diagnoses:
            diagnosis_texts = []
            for diagnosis in diagnoses:
                diag_text = f"Diagnosis: {diagnosis.get('name', 'Unknown')}"
                if diagnosis.get('code') != "Not Available":
                    diag_text += f" (Code: {diagnosis.get('code')})"
                if diagnosis.get('date_diagnosed') != "Not Available":
                    diag_text += f" diagnosed on {diagnosis.get('date_diagnosed')}"
                diagnosis_texts.append(diag_text)
            summaries["diagnoses_summary"] = ". ".join(diagnosis_texts)
        
        # Procedures summary
        procedures = clinical_data.get("procedures", [])
        if procedures:
            procedure_texts = []
            for procedure in procedures:
                proc_text = f"Procedure: {procedure.get('name', 'Unknown')}"
                if procedure.get('date') != "Not Available":
                    proc_text += f" performed on {procedure.get('date')}"
                if procedure.get('outcome') != "Not Available":
                    proc_text += f" with outcome: {procedure.get('outcome')}"
                procedure_texts.append(proc_text)
            summaries["procedures_summary"] = ". ".join(procedure_texts)
        
        # Medications summary
        medications = clinical_data.get("medications", [])
        if medications:
            med_texts = []
            for medication in medications:
                med_text = f"Medication: {medication.get('name', 'Unknown')}"
                if medication.get('dosage') != "Not Available":
                    med_text += f" {medication.get('dosage')}"
                if medication.get('frequency') != "Not Available":
                    med_text += f" {medication.get('frequency')}"
                med_texts.append(med_text)
            summaries["medications_summary"] = ". ".join(med_texts)
        
        # Timeline summary
        timeline = clinical_data.get("timeline", [])
        if timeline:
            timeline_texts = []
            for event in timeline:
                timeline_text = f"Event on {event.get('date', 'unknown date')}: {event.get('event', 'Unknown event')}"
                timeline_texts.append(timeline_text)
            summaries["timeline_summary"] = ". ".join(timeline_texts)
        
        return summaries


class EmbeddingGeneratorTool(BaseTool):
    """Tool for generating embeddings using OpenAI."""
    
    name: str = "embedding_generator"
    description: str = "Generate embeddings for text chunks using OpenAI API"
    
    def _run(self, chunks: List[Dict[str, Any]], model: str = "text-embedding-ada-002") -> Dict[str, Any]:
        """Generate embeddings for text chunks."""
        try:
            import openai
            from src.config.settings import settings
            
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=settings.openai_api_key)
            
            embeddings = []
            
            # Process chunks in batches
            batch_size = 10
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_texts = [chunk["text"] for chunk in batch]
                
                # Generate embeddings
                response = client.embeddings.create(
                    input=batch_texts,
                    model=model
                )
                
                # Process results
                for j, embedding_data in enumerate(response.data):
                    chunk_idx = i + j
                    chunk = batch[chunk_idx]
                    
                    embeddings.append({
                        "chunk_id": chunk["chunk_id"],
                        "vector": embedding_data.embedding,
                        "metadata": {
                            **chunk["metadata"],
                            "embedding_model": model,
                            "embedding_dimension": len(embedding_data.embedding),
                            "embedded_at": datetime.utcnow().isoformat()
                        }
                    })
            
            logger.info(f"Generated {len(embeddings)} embeddings successfully")
            
            return {
                "success": True,
                "embeddings": embeddings,
                "model": model,
                "total_embeddings": len(embeddings)
            }
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "embeddings": []
            }


class MilvusStorageTool(BaseTool):
    """Tool for storing embeddings in Milvus."""
    
    name: str = "milvus_storage"
    description: str = "Store embeddings and metadata in Milvus vector database"
    
    def _run(self, embeddings: List[Dict[str, Any]], collection_name: str = "medical_documents") -> Dict[str, Any]:
        """Store embeddings in Milvus."""
        try:
            logger.info(f"Storing {len(embeddings)} embeddings in Milvus")
            
            milvus_client = get_milvus()
            
            # Prepare data for insertion
            entities = []
            for embedding in embeddings:
                entity = {
                    "id": self._generate_id(embedding["chunk_id"]),
                    "vector": embedding["vector"],
                    "patient_id": embedding["metadata"].get("patient_id", ""),
                    "document_id": embedding["metadata"].get("document_id", ""),
                    "section": embedding["metadata"].get("section", ""),
                    "chunk_type": embedding["metadata"].get("chunk_type", ""),
                    "text_length": embedding["metadata"].get("text_length", 0),
                    "document_date": embedding["metadata"].get("document_date", ""),
                    "embedding_model": embedding["metadata"].get("embedding_model", ""),
                    "embedded_at": embedding["metadata"].get("embedded_at", ""),
                    "metadata_json": json.dumps(embedding["metadata"])
                }
                entities.append(entity)
            
            # Insert into Milvus
            result = milvus_client.insert_embeddings(entities, collection_name)
            
            logger.info(f"Successfully stored {len(entities)} embeddings in Milvus")
            
            return {
                "success": True,
                "inserted_count": len(entities),
                "collection_name": collection_name,
                "milvus_result": result
            }
            
        except Exception as e:
            logger.error(f"Milvus storage failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "inserted_count": 0
            }
    
    def _generate_id(self, chunk_id: str) -> int:
        """Generate numeric ID from chunk_id for Milvus."""
        return int(hashlib.md5(chunk_id.encode()).hexdigest()[:8], 16)


class VectorEmbeddingAgent:
    """CrewAI agent for text embedding and vector storage."""
    
    def __init__(self):
        self.chunking_tool = TextChunkingTool()
        self.embedding_tool = EmbeddingGeneratorTool()
        self.storage_tool = MilvusStorageTool()
        
        self.agent = Agent(
            role="Vector Embedding and Storage Specialist",
            goal="Convert clinical text into high-quality embeddings and store them efficiently for semantic search",
            backstory="""You are a specialist in natural language processing and vector databases 
            with deep expertise in medical text processing. You understand how to chunk clinical 
            documents to preserve semantic meaning while optimizing for retrieval. You have experience 
            with embedding models, vector databases like Milvus, and the specific challenges of 
            medical text embedding including handling of medical terminology, structured data, 
            and maintaining patient data isolation.""",
            tools=[self.chunking_tool, self.embedding_tool, self.storage_tool],
            verbose=True,
            allow_delegation=False,
            max_iter=2
        )
    
    def create_embedding_task(self, clinical_data: Dict[str, Any], document_id: str) -> Task:
        """Create a task for text embedding and storage."""
        
        return Task(
            description=f"""
            Process the extracted clinical data for vector embedding and storage.
            
            Clinical Data: {json.dumps(clinical_data, indent=2)}
            Document ID: {document_id}
            
            Your task involves three main steps:
            
            1. **Text Chunking**: 
               - Split the clinical text into meaningful chunks for embedding
               - Focus on SOAP note sections (Subjective, Objective, Assessment, Plan)
               - Include narrative sections (feedback, recovery progress, patient history)
               - Create structured summaries of injuries, diagnoses, procedures, medications
               - Maintain optimal chunk sizes (200-300 tokens) with appropriate overlap
               - Preserve semantic coherence within each chunk
            
            2. **Embedding Generation**:
               - Generate high-quality embeddings for each text chunk
               - Use appropriate embedding model (text-embedding-ada-002)
               - Include embedding metadata (model, dimensions, timestamp)
               - Ensure embeddings capture medical semantic meaning
            
            3. **Vector Storage**:
               - Store embeddings in Milvus vector database
               - Include comprehensive metadata for each vector:
                 * patient_id (for data isolation)
                 * document_id (for traceability)
                 * section type (subjective, objective, etc.)
                 * chunk type (soap_section, narrative, structured_summary)
                 * document date and title
                 * embedding model and parameters
               - Ensure proper indexing for efficient similarity search
               - Maintain referential integrity with structured data
            
            **Critical Requirements**:
            - Preserve patient_id in all vector metadata for data isolation
            - Include document_id for traceability back to original source
            - Maintain section context for targeted retrieval
            - Optimize chunk boundaries to preserve clinical meaning
            - Store sufficient metadata for comprehensive provenance tracking
            
            Return a summary of the embedding process including:
            - Number of chunks created
            - Number of embeddings generated
            - Storage confirmation in Milvus
            - Any errors or warnings
            """,
            expected_output="Complete embedding process summary with chunk count, embedding count, and storage confirmation",
            agent=self.agent
        )
    
    def process_embeddings(self, clinical_data: Dict[str, Any], document_id: str) -> Dict[str, Any]:
        """Process clinical data for embedding and storage."""
        try:
            logger.info(f"Starting embedding process for document {document_id}")
            
            # Step 1: Chunk text
            chunking_result = self.chunking_tool._run(clinical_data)
            if not chunking_result["success"]:
                return {
                    "success": False,
                    "error": f"Chunking failed: {chunking_result['error']}",
                    "stage": "chunking"
                }
            
            chunks = chunking_result["chunks"]
            if not chunks:
                return {
                    "success": False,
                    "error": "No text chunks created",
                    "stage": "chunking"
                }
            
            # Step 2: Generate embeddings
            embedding_result = self.embedding_tool._run(chunks)
            if not embedding_result["success"]:
                return {
                    "success": False,
                    "error": f"Embedding generation failed: {embedding_result['error']}",
                    "stage": "embedding"
                }
            
            embeddings = embedding_result["embeddings"]
            
            # Step 3: Store in Milvus
            storage_result = self.storage_tool._run(embeddings)
            if not storage_result["success"]:
                return {
                    "success": False,
                    "error": f"Milvus storage failed: {storage_result['error']}",
                    "stage": "storage"
                }
            
            return {
                "success": True,
                "chunks_created": len(chunks),
                "embeddings_generated": len(embeddings),
                "embeddings_stored": storage_result["inserted_count"],
                "collection_name": storage_result["collection_name"],
                "embedding_model": embedding_result["model"]
            }
            
        except Exception as e:
            logger.error(f"Embedding process failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "stage": "unknown"
            }
