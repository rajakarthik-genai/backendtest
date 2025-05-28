# File: db/milvus_db.py
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility

class MilvusDB:
    """
    Milvus client for storing and retrieving vector embeddings (e.g. for RAG).
    """
    def __init__(self, host="localhost", port="19530", collection_name="embeddings", dim=1536):
        self.collection_name = collection_name
        self.dim = dim
        # Connect to Milvus server
        connections.connect("default", host=host, port=port)
        # Create collection if not exists
        if not utility.has_collection(self.collection_name):
            self._create_collection()
        else:
            self.collection = Collection(self.collection_name)
            # (Milvus retains indexes on created collections)

    def _create_collection(self):
        # Define collection schema
        id_field = FieldSchema(name="doc_id", dtype=DataType.INT64, is_primary=True, auto_id=False)
        vector_field = FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim)
        schema = CollectionSchema(fields=[id_field, vector_field], description="Document embeddings")
        self.collection = Collection(self.collection_name, schema)
        # Create a vector index for efficient search
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "L2",
            "params": {"nlist": 100}
        }
        self.collection.create_index("embedding", index_params)
        # Load collection into memory for search
        self.collection.load()

    def insert_embedding(self, doc_id, vector):
        """
        Insert a new embedding vector with associated doc_id.
        """
        entities = [
            [doc_id],  # primary key field
            [vector]   # embedding field
        ]
        insert_result = self.collection.insert(entities)
        return insert_result

    def search(self, vector, top_k=5):
        """
        Search the vector store for the nearest neighbors of the given vector.
        """
        self.collection.load()
        search_params = {"metric_type": "L2"}
        results = self.collection.search([vector], "embedding", search_params, limit=top_k, output_fields=["doc_id"])
        # Format results as list of (id, distance)
        neighbors = []
        for hits in results:
            for hit in hits:
                neighbors.append({"doc_id": hit.entity.get("doc_id"), "distance": hit.distance})
        return neighbors

    def drop_collection(self):
        """
        Drop the entire collection (careful: deletes all data).
        """
        utility.drop_collection(self.collection_name)
