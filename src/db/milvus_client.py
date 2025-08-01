"""
Milvus vector database client for similarity search
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
import json
import numpy as np
from pymilvus import (
    connections, Collection, FieldSchema, CollectionSchema, 
    DataType, utility, MilvusException
)

from src.core.config import settings

logger = logging.getLogger(__name__)

class MilvusClient:
    """Milvus vector database client"""
    
    def __init__(self):
        self.host = settings.MILVUS_HOST
        self.port = settings.MILVUS_PORT
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self.dim = settings.MILVUS_DIM
        self.collection = None
        self._connect()
    
    def _connect(self):
        """Connect to Milvus"""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port,
                timeout=30
            )
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise
    
    async def initialize_collections(self):
        """Initialize Milvus collections"""
        try:
            # Check if collection exists
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                logger.info(f"Using existing collection: {self.collection_name}")
            else:
                # Create collection
                self._create_collection()
            
            # Load collection to memory
            self.collection.load()
            logger.info("Milvus collection loaded to memory")
            
        except Exception as e:
            logger.error(f"Failed to initialize Milvus collections: {e}")
            raise
    
    def _create_collection(self):
        """Create Milvus collection with schema"""
        try:
            # Define schema
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
                FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="patient_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=8192),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
                FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=2048)
            ]
            
            schema = CollectionSchema(
                fields=fields,
                description="Medical document embeddings"
            )
            
            # Create collection
            self.collection = Collection(
                name=self.collection_name,
                schema=schema,
                consistency_level="Strong"
            )
            
            # Create indexes
            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "L2",
                "params": {"nlist": 1024}
            }
            
            self.collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            
            logger.info(f"Created Milvus collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to create Milvus collection: {e}")
            raise
    
    async def insert_embeddings(self, embeddings_data: List[Dict[str, Any]]):
        """Insert embeddings into Milvus"""
        try:
            if not self.collection:
                raise RuntimeError("Collection not initialized")
            
            # Prepare data for insertion
            ids = []
            document_ids = []
            patient_ids = []
            chunk_ids = []
            texts = []
            embeddings = []
            metadatas = []
            
            for data in embeddings_data:
                # Generate unique ID
                unique_id = f"{data['patient_id']}_{data['chunk_id']}"
                ids.append(unique_id)
                document_ids.append(data['document_id'])
                patient_ids.append(data['patient_id'])
                chunk_ids.append(data['chunk_id'])
                texts.append(data['text'][:8192])  # Truncate if needed
                embeddings.append(data['embedding'])
                metadatas.append(json.dumps(data.get('metadata', {}))[:2048])
            
            # Insert data
            entities = [
                ids,
                document_ids,
                patient_ids,
                chunk_ids,
                texts,
                embeddings,
                metadatas
            ]
            
            self.collection.insert(entities)
            self.collection.flush()
            
            logger.info(f"Inserted {len(embeddings_data)} embeddings into Milvus")
            
        except Exception as e:
            logger.error(f"Failed to insert embeddings: {e}")
            raise

    async def insert_document(
        self, 
        document_id: str, 
        patient_id: str, 
        text: str, 
        embedding: List[float], 
        metadata: Dict[str, Any] = None
    ):
        """Insert a single document embedding into Milvus"""
        try:
            if not self.collection:
                raise RuntimeError("Collection not initialized")
            
            # Generate unique ID and chunk ID
            chunk_id = f"chunk_{uuid.uuid4().hex[:8]}"
            unique_id = f"{patient_id}_{chunk_id}"
            
            # Prepare data
            entities = [
                [unique_id],                                    # ids
                [document_id],                                  # document_ids
                [patient_id],                                   # patient_ids
                [chunk_id],                                     # chunk_ids
                [text[:8192]],                                  # texts (truncated)
                [embedding],                                    # embeddings
                [json.dumps(metadata or {})[:2048]]             # metadata (truncated)
            ]
            
            # Insert data
            self.collection.insert(entities)
            self.collection.flush()
            
            logger.info(f"Inserted document embedding: {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to insert document embedding: {e}")
            raise
    
    async def search_similar(
        self, 
        query_embedding: List[float], 
        patient_id: str,
        top_k: int = 10,
        filter_expression: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            if not self.collection:
                raise RuntimeError("Collection not initialized")
            
            # Build filter expression
            if not filter_expression:
                filter_expression = f'patient_id == "{patient_id}"'
            else:
                filter_expression = f'patient_id == "{patient_id}" and {filter_expression}'
            
            # Search parameters
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }
            
            # Perform search
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=filter_expression,
                output_fields=["document_id", "chunk_id", "text", "metadata"]
            )
            
            # Format results
            formatted_results = []
            for hits in results:
                for hit in hits:
                    formatted_results.append({
                        "id": hit.id,
                        "distance": hit.distance,
                        "document_id": hit.entity.get("document_id"),
                        "chunk_id": hit.entity.get("chunk_id"),
                        "text": hit.entity.get("text"),
                        "metadata": json.loads(hit.entity.get("metadata", "{}"))
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    async def delete_document_embeddings(self, document_id: str):
        """Delete all embeddings for a document"""
        try:
            if not self.collection:
                raise RuntimeError("Collection not initialized")
            
            expr = f'document_id == "{document_id}"'
            self.collection.delete(expr)
            self.collection.flush()
            
            logger.info(f"Deleted embeddings for document: {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete embeddings: {e}")
            raise
    
    def is_healthy(self) -> bool:
        """Check if Milvus connection is healthy"""
        try:
            # Check connection
            return utility.list_collections() is not None
        except:
            return False
    
    def close(self):
        """Close Milvus connection"""
        try:
            if self.collection:
                self.collection.release()
            connections.disconnect("default")
            logger.info("Milvus connection closed")
        except Exception as e:
            logger.error(f"Error closing Milvus connection: {e}")
