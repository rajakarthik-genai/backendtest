"""
Milvus vector database for medical document embeddings and semantic search.

Handles:
- Document embedding storage and retrieval
- Semantic similarity search
- User data isolation via metadata filtering
- Multi-modal embedding support
"""

import hashlib
import hmac
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    from pymilvus import (
        connections, FieldSchema, CollectionSchema, DataType, 
        Collection, utility, MilvusException
    )
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from src.config.settings import settings
from src.utils.logging import logger


class MilvusDB:
    """Milvus vector database manager for medical document embeddings."""
    
    def __init__(self):
        self.connection = None
        self.collection = None
        self.embedding_model = None
        self._initialized = False
        self.collection_name = "medical_knowledge"
        self.embedding_dim = 384  # all-MiniLM-L6-v2 dimension
    
    def initialize(self, host: str = "localhost", port: int = 19530):
        """Initialize Milvus connection and collection."""
        if not MILVUS_AVAILABLE:
            logger.error("Milvus dependencies not installed")
            raise ImportError("pymilvus not available")
        
        try:
            # Connect to Milvus
            connections.connect(
                alias="default",
                host=host,
                port=str(port)
            )
            
            # Initialize embedding model
            self._init_embedding_model()
            
            # Create or connect to collection
            self._init_collection()
            
            self._initialized = True
            logger.info(f"Milvus connected to {host}:{port}")
            
        except Exception as e:
            logger.error(f"Milvus initialization failed: {e}")
            raise
    
    def _init_embedding_model(self):
        """Initialize sentence transformer model for embeddings."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("SentenceTransformers not available, using mock embeddings")
            return
        
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded: all-MiniLM-L6-v2")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _init_collection(self):
        """Create or connect to Milvus collection."""
        try:
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                logger.info(f"Connected to existing collection: {self.collection_name}")
            else:
                self._create_collection()
                logger.info(f"Created new collection: {self.collection_name}")
            
            # Load collection into memory
            self.collection.load()
            
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise
    
    def _create_collection(self):
        """Create new Milvus collection with schema."""
        try:
            fields = [
                FieldSchema(
                    name="id",
                    dtype=DataType.INT64,
                    is_primary=True,
                    auto_id=True
                ),
                FieldSchema(
                    name="user_id_hash",
                    dtype=DataType.VARCHAR,
                    max_length=64
                ),
                FieldSchema(
                    name="document_id",
                    dtype=DataType.VARCHAR,
                    max_length=64
                ),
                FieldSchema(
                    name="content",
                    dtype=DataType.VARCHAR,
                    max_length=65535
                ),
                FieldSchema(
                    name="embedding",
                    dtype=DataType.FLOAT_VECTOR,
                    dim=self.embedding_dim
                ),
                FieldSchema(
                    name="metadata",
                    dtype=DataType.JSON
                ),
                FieldSchema(
                    name="timestamp",
                    dtype=DataType.VARCHAR,
                    max_length=32
                )
            ]
            
            schema = CollectionSchema(
                fields,
                description="Medical knowledge embeddings with user isolation"
            )
            
            self.collection = Collection(
                name=self.collection_name,
                schema=schema
            )
            
            # Create index for vector similarity search
            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "L2",
                "params": {"nlist": 1024}
            }
            
            self.collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            
            logger.info("Milvus collection and index created")
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    def _hash_user_id(self, user_id: str, secret_key: str = None) -> str:
        """Create consistent hash of user_id for data isolation."""
        if not secret_key:
            secret_key = settings.milvus_uri
        
        return hmac.new(
            secret_key.encode(),
            user_id.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        if not self.embedding_model:
            # Mock embedding for testing
            return [0.1] * self.embedding_dim
        
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return [0.0] * self.embedding_dim
    
    def store_document_embeddings(
        self,
        user_id: str,
        document_id: str,
        text_chunks: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[int]:
        """Store document embeddings in Milvus."""
        if not self._initialized:
            raise RuntimeError("Milvus not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            # Prepare data for insertion
            embeddings = []
            contents = []
            user_ids = []
            document_ids = []
            metadatas = []
            timestamps = []
            
            current_time = datetime.utcnow().isoformat()
            
            for chunk in text_chunks:
                if not chunk.strip():
                    continue
                
                embedding = self._generate_embedding(chunk)
                
                embeddings.append(embedding)
                contents.append(chunk[:65000])  # Truncate if too long
                user_ids.append(hashed_user_id)
                document_ids.append(document_id)
                metadatas.append(metadata or {})
                timestamps.append(current_time)
            
            if not embeddings:
                return []
            
            # Insert data
            entities = [
                user_ids,      # user_id_hash
                document_ids,  # document_id
                contents,      # content
                embeddings,    # embedding
                metadatas,     # metadata
                timestamps     # timestamp
            ]
            
            insert_result = self.collection.insert(entities)
            self.collection.flush()
            
            logger.info(f"Stored {len(embeddings)} embeddings for document {document_id}")
            return insert_result.primary_keys
            
        except Exception as e:
            logger.error(f"Failed to store embeddings: {e}")
            raise
    
    def search_similar_documents(
        self,
        user_id: str,
        query_text: str,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using vector similarity."""
        if not self._initialized:
            raise RuntimeError("Milvus not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            # Generate query embedding
            query_embedding = self._generate_embedding(query_text)
            
            # Define search parameters
            search_params = {
                "metric_type": "L2",
                "params": {"nprobe": 10}
            }
            
            # Search with user isolation filter
            expr = f'user_id_hash == "{hashed_user_id}"'
            
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=limit,
                expr=expr,
                output_fields=["content", "document_id", "metadata", "timestamp"]
            )
            
            # Process results
            similar_docs = []
            for hit in results[0]:
                if hit.distance <= score_threshold:
                    similar_docs.append({
                        "content": hit.entity.get("content"),
                        "document_id": hit.entity.get("document_id"),
                        "metadata": hit.entity.get("metadata"),
                        "timestamp": hit.entity.get("timestamp"),
                        "similarity_score": 1.0 / (1.0 + hit.distance)  # Convert distance to similarity
                    })
            
            return similar_docs
            
        except Exception as e:
            logger.error(f"Failed to search similar documents: {e}")
            return []
    
    def get_user_documents(
        self,
        user_id: str,
        document_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all document chunks for a user."""
        if not self._initialized:
            raise RuntimeError("Milvus not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            # Build expression for filtering
            expr = f'user_id_hash == "{hashed_user_id}"'
            if document_id:
                expr += f' && document_id == "{document_id}"'
            
            # Query documents
            results = self.collection.query(
                expr=expr,
                output_fields=["content", "document_id", "metadata", "timestamp"],
                limit=limit
            )
            
            documents = []
            for result in results:
                documents.append({
                    "content": result.get("content"),
                    "document_id": result.get("document_id"),
                    "metadata": result.get("metadata"),
                    "timestamp": result.get("timestamp")
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to get user documents: {e}")
            return []
    
    def delete_user_data(self, user_id: str) -> bool:
        """Delete all data for a specific user."""
        if not self._initialized:
            raise RuntimeError("Milvus not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            expr = f'user_id_hash == "{hashed_user_id}"'
            self.collection.delete(expr)
            self.collection.flush()
            
            logger.info(f"Deleted all data for user {user_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete user data: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        if not self._initialized:
            raise RuntimeError("Milvus not initialized")
        
        try:
            stats = self.collection.num_entities
            return {
                "total_entities": stats,
                "collection_name": self.collection_name,
                "embedding_dimension": self.embedding_dim
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    def close(self):
        """Close Milvus connection."""
        try:
            if self.collection:
                self.collection.release()
            connections.disconnect("default")
            logger.info("Milvus connection closed")
        except Exception as e:
            logger.error(f"Error closing Milvus connection: {e}")


# Global Milvus instance
milvus_db = MilvusDB()


def init_milvus(host: str, port: int = 19530):
    """Initialize global Milvus instance."""
    milvus_db.initialize(host, port)


def get_milvus() -> MilvusDB:
    """Get Milvus instance."""
    if not milvus_db._initialized:
        raise RuntimeError("Milvus not initialized. Call init_milvus() first.")
    return milvus_db
