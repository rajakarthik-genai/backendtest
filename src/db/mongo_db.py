# File: db/mongo_db.py
from src.config.settings import settings
from pymongo import MongoClient
from bson import ObjectId
import datetime

class MongoDB:
    """
    MongoDB client with schema validation and indexing for the digital twin backend.
    """
    def __init__(self, uri=None, db_name=None):
        uri = uri or settings.MONGO_URI
        if not db_name:
            # Try to extract db from URI, else fallback
            if "/" in uri.rsplit("@", 1)[-1]:
                db_name = uri.rsplit("/", 1)[-1]
            else:
                db_name = "digital_twin"
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self._setup_collections()

    def _setup_collections(self):
        # Define JSON schema validators for collections
        user_schema = {
            'bsonType': 'object',
            'required': ['first_name', 'last_name'],
            'properties': {
                'first_name': {'bsonType': 'string'},
                'last_name': {'bsonType': 'string'},
                'dob': {'bsonType': 'date'},
                'gender': {
                    'enum': ['Male', 'Female', 'Other'],
                    'description': 'Gender of the patient'
                },
                'email': {
                    'bsonType': 'string',
                    'pattern': r'^\S+@\S+\.\S+$',
                    'description': 'Must be a valid email address'
                }
            }
        }
        report_schema = {
            'bsonType': 'object',
            'required': ['patient_id', 'content'],
            'properties': {
                'patient_id': {'bsonType': 'objectId'},
                'content': {'bsonType': 'string'},
                'uploaded_at': {'bsonType': 'date'},
                'file_name': {'bsonType': 'string'}
            }
        }
        event_schema = {
            'bsonType': 'object',
            'required': ['patient_id', 'event_type', 'timestamp'],
            'properties': {
                'patient_id': {'bsonType': 'objectId'},
                'event_type': {'bsonType': 'string'},
                'description': {'bsonType': 'string'},
                'timestamp': {'bsonType': 'date'}
            }
        }
        # Create or get collections with validators
        if "users" not in self.db.list_collection_names():
            self.db.create_collection("users", validator={'$jsonSchema': user_schema})
        if "reports" not in self.db.list_collection_names():
            self.db.create_collection("reports", validator={'$jsonSchema': report_schema})
        if "health_events" not in self.db.list_collection_names():
            self.db.create_collection("health_events", validator={'$jsonSchema': event_schema})

        # Create indexes for efficient queries
        self.db.users.create_index("email", unique=True)
        self.db.users.create_index("last_name")
        self.db.reports.create_index("patient_id")
        self.db.health_events.create_index("patient_id")
        self.db.health_events.create_index("timestamp")

    # CRUD operations for Users
    def create_user(self, first_name, last_name, dob=None, gender=None, email=None):
        """
        Insert a new user document into the users collection.
        """
        user = {
            "first_name": first_name,
            "last_name": last_name,
            "dob": dob if dob else datetime.datetime.utcnow(),
            "gender": gender,
            "email": email
        }
        result = self.db.users.insert_one(user)
        return str(result.inserted_id)

    def get_user(self, user_id):
        """
        Retrieve a user document by its ObjectId.
        """
        result = self.db.users.find_one({"_id": ObjectId(user_id)})
        if result:
            result["_id"] = str(result["_id"])
        return result

    def update_user(self, user_id, updates: dict):
        """
        Update fields of a user document.
        """
        self.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})

    def delete_user(self, user_id):
        """
        Delete a user document.
        """
        self.db.users.delete_one({"_id": ObjectId(user_id)})

    # CRUD operations for Reports
    def create_report(self, patient_id, content, file_name=None):
        """
        Insert a new report document for a patient.
        """
        report = {
            "patient_id": ObjectId(patient_id),
            "content": content,
            "file_name": file_name,
            "uploaded_at": datetime.datetime.utcnow()
        }
        result = self.db.reports.insert_one(report)
        return str(result.inserted_id)

    def get_report(self, report_id):
        """
        Retrieve a report by its ObjectId.
        """
        result = self.db.reports.find_one({"_id": ObjectId(report_id)})
        if result:
            result["_id"] = str(result["_id"])
            result["patient_id"] = str(result["patient_id"])
        return result

    def update_report(self, report_id, updates: dict):
        """
        Update fields of a report document.
        """
        self.db.reports.update_one({"_id": ObjectId(report_id)}, {"$set": updates})

    def delete_report(self, report_id):
        """
        Delete a report document.
        """
        self.db.reports.delete_one({"_id": ObjectId(report_id)})

    # CRUD operations for Health Events
    def create_health_event(self, patient_id, event_type, description=None, timestamp=None):
        """
        Insert a health event associated with a patient.
        """
        event = {
            "patient_id": ObjectId(patient_id),
            "event_type": event_type,
            "description": description,
            "timestamp": timestamp if timestamp else datetime.datetime.utcnow()
        }
        result = self.db.health_events.insert_one(event)
        return str(result.inserted_id)

    def get_health_event(self, event_id):
        """
        Retrieve a health event by its ObjectId.
        """
        result = self.db.health_events.find_one({"_id": ObjectId(event_id)})
        if result:
            result["_id"] = str(result["_id"])
            result["patient_id"] = str(result["patient_id"])
        return result

    def update_health_event(self, event_id, updates: dict):
        """
        Update fields of a health event.
        """
        self.db.health_events.update_one({"_id": ObjectId(event_id)}, {"$set": updates})

    def delete_health_event(self, event_id):
        """
        Delete a health event document.
        """
        self.db.health_events.delete_one({"_id": ObjectId(event_id)})
