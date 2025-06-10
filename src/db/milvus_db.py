# Dependencies: Milvus (pymilvus), SentenceTransformers (sentence_transformers)
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # Handle case where no local embedding model is used

class MilvusIndexer:
    """
    Milvus client for managing vector embeddings of document content for semantic search.
    Connects to Milvus, ensures collection schema, and provides methods to insert and search embeddings.
    """
    def __init__(self, host: str = "localhost", port: int = 19530, collection_name: str = "medical_embeddings", embedding_model_name: str = None):
        # Connect to Milvus server
        connections.connect(alias="default", host=host, port=str(port))
        self.collection_name = collection_name
        self.collection = None
        # If an embedding model name is provided, load the model for computing embeddings
        self.model = None
        if embedding_model_name and SentenceTransformer:
            self.model = SentenceTransformer(embedding_model_name)
        # If collection exists, get it; otherwise, it will be created on first insert
        if utility.has_collection(collection_name):
            self.collection = Collection(collection_name)
    
    def _ensure_collection(self, dim: int):
        """Ensure the Milvus collection exists with the proper schema (called on first insert)."""
        if not utility.has_collection(self.collection_name):
            fields = [
                FieldSchema(name="patient_id", dtype=DataType.VARCHAR, max_length=100),  # patient identifier
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)
            ]
            schema = CollectionSchema(fields, description="Medical document embeddings for semantic search")
            self.collection = Collection(name=self.collection_name, schema=schema, using="default", shards_num=1)
            # Create an index on the embedding field for efficient search
            index_params = {"index_type": "IVF_FLAT", "metric_type": "L2", "params": {"nlist": 128}}
            self.collection.create_index(field_name="embedding", index_params=index_params)
    
    def embed_text(self, text: str):
        """
        Generate embedding vector for the given text using the loaded model.
        Returns a list of float values representing the embedding.
        """
        if not self.model:
            raise RuntimeError("No embedding model is loaded for MilvusIndexer")
        vec = self.model.encode(text)
        # Convert to list for storage
        try:
            vec = vec.tolist()
        except AttributeError:
            vec = list(vec)
        return vec
    
    def insert_text(self, patient_id: str, text: str):
        """
        Compute the embedding for the given text and insert it into Milvus with the patient_id.
        """
        embedding = self.embed_text(text)
        self.insert_embedding(patient_id, embedding)
    
    def insert_embedding(self, patient_id: str, embedding: list):
        """
        Insert a pre-computed embedding vector into Milvus, associating it with a patient_id.
        """
        if embedding is None:
            return
        # If collection not initialized, create it with the given embedding dimension
        self._ensure_collection(dim=len(embedding))
        # Prepare data in columnar format: [[patient_ids], [embedding_vectors]]
        data = [[str(patient_id)], [embedding]]
        self.collection.insert(data)
        # Flush to make sure data is persisted and indexed
        self.collection.flush()
    
    def search(self, query_text: str, top_k: int = 5, filter_patient_id: str = None):
        """
        Search for vectors similar to the embedding of the query_text.
        Returns a list of hits with their distances and associated patient_id.
        If filter_patient_id is provided, restrict search to that patient only.
        """
        if self.collection is None:
            return []
        # Compute embedding for the query text
        query_vec = None
        if self.model:
            query_vec = self.model.encode(query_text)
            try:
                query_vec = query_vec.tolist()
            except AttributeError:
                query_vec = list(query_vec)
        else:
            raise RuntimeError("No embedding model loaded to perform search")
        # Load collection into memory if not already
        self.collection.load()
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        # Use filter expression if patient_id filter is given
        expr = None
        if filter_patient_id:
            expr = f'patient_id == "{filter_patient_id}"'
        results = self.collection.search([query_vec], "embedding", param=search_params, limit=top_k, expr=expr, output_fields=["patient_id"])
        hits = []
        if results and len(results) > 0:
            for hit in results[0]:
                hit_info = {
                    "id": hit.id,
                    "distance": hit.distance,
                    "patient_id": hit.entity.get("patient_id")
                }
                hits.append(hit_info)
        return hits
