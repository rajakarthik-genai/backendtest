# Dependencies: PyMongo (pymongo)
from pymongo import MongoClient
from datetime import datetime

class MongoDBClient:
    """
    MongoDB client for storing and retrieving medical records.
    Provides methods to insert structured records and query by patient/timeline.
    """
    def __init__(self, uri: str, db_name: str, collection_name: str = "medical_records"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        # Ensure index on patient_id and timestamp for fast timeline queries
        self.collection.create_index([("patient_id", 1), ("timestamp", 1)])
    
    def insert_records(self, records):
        """
        Insert one or multiple records (dict or list of dicts) into MongoDB.
        Each record should contain patient_id, timestamp, metric_name, value, unit, source.
        """
        if records is None:
            return
        if isinstance(records, dict):
            records = [records]
        if len(records) == 0:
            return
        # Ensure timestamp is datetime for proper sorting/indexing
        for rec in records:
            if rec.get("timestamp") and not isinstance(rec["timestamp"], datetime):
                try:
                    rec["timestamp"] = datetime.fromisoformat(str(rec["timestamp"]))
                except Exception:
                    # If parsing fails, default to current time
                    rec["timestamp"] = datetime.now()
        self.collection.insert_many(records)
    
    def query_timeline(self, patient_id: str, start_date=None, end_date=None):
        """
        Retrieve all records for a given patient_id, optionally within a date range.
        Returns a list of records sorted by timestamp.
        """
        query = {"patient_id": patient_id}
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                # ensure datetime for query
                query["timestamp"]["$gte"] = start_date if isinstance(start_date, datetime) else datetime.fromisoformat(str(start_date))
            if end_date:
                query["timestamp"]["$lte"] = end_date if isinstance(end_date, datetime) else datetime.fromisoformat(str(end_date))
        cursor = self.collection.find(query).sort("timestamp", 1)
        return list(cursor)
    
    def get_records_by_metric(self, patient_id: str, metric_name: str):
        """
        Retrieve all records for a given patient and metric name, sorted by time.
        """
        cursor = self.collection.find({"patient_id": patient_id, "metric_name": metric_name}).sort("timestamp", 1)
        return list(cursor)
    
    def close(self):
        """Close the MongoDB connection."""
        self.client.close()
