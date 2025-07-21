"""
MongoDB connection and operations for medical records and PII data.

Handles:
- Medical records with encrypted PII fields
- User data isolation via user_id filtering
- Document storage and retrieval
- Timeline and event data
"""

import hashlib
import hmac
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, OperationFailure
from bson import ObjectId

from src.config.settings import settings
from src.utils.logging import logger


class MongoDB:
    """MongoDB operations manager with encryption and user isolation."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._initialized = False
    
    async def initialize(self, mongo_uri: str, db_name: str = "digital_twin"):
        """Initialize MongoDB connection."""
        try:
            self.client = AsyncIOMotorClient(mongo_uri)
            self.db = self.client[db_name]
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Create indexes for performance and security
            await self._create_indexes()
            
            self._initialized = True
            logger.info(f"MongoDB connected to {db_name}")
            
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise
    
    async def _create_indexes(self):
        """Create necessary indexes for performance and data isolation."""
        try:
            # Medical records collection
            await self.db.medical_records.create_index([("user_id", 1)])
            await self.db.medical_records.create_index([("user_id", 1), ("timestamp", -1)])
            await self.db.medical_records.create_index([("user_id", 1), ("record_type", 1)])
            
            # PII collection
            await self.db.user_pii.create_index([("user_id", 1)], unique=True)
            
            # Timeline events
            await self.db.timeline_events.create_index([("user_id", 1), ("timestamp", -1)])
            await self.db.timeline_events.create_index([("user_id", 1), ("event_type", 1)])
            
            # Document metadata
            await self.db.document_metadata.create_index([("user_id", 1)])
            await self.db.document_metadata.create_index([("user_id", 1), ("filename", 1)])
            
            logger.info("MongoDB indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create MongoDB indexes: {e}")
            raise
    
    def _hash_user_id(self, user_id: str, secret_key: str = None) -> str:
        """Create consistent hash of user_id for data isolation."""
        if not secret_key:
            secret_key = settings.mongo_initdb_root_password
        
        return hmac.new(
            secret_key.encode(),
            user_id.encode(),
            hashlib.sha256
        ).hexdigest()
    
    async def store_medical_record(
        self,
        user_id: str,
        record_data: Dict[str, Any],
        record_type: str = "general"
    ) -> str:
        """Store a medical record with user isolation."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            medical_record = {
                "user_id": hashed_user_id,
                "record_id": str(ObjectId()),
                "record_type": record_type,
                "data": record_data,
                "timestamp": datetime.utcnow(),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.db.medical_records.insert_one(medical_record)
            
            logger.info(f"Medical record stored for user {user_id[:8]}...")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to store medical record: {e}")
            raise
    
    async def get_medical_records(
        self,
        user_id: str,
        record_type: Optional[str] = None,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve medical records for a user."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            query = {"user_id": hashed_user_id}
            if record_type:
                query["record_type"] = record_type
            
            # Add additional filters if provided
            if filters:
                query.update(filters)
            
            cursor = self.db.medical_records.find(query).sort("timestamp", -1).skip(offset).limit(limit)
            records = await cursor.to_list(length=limit)
            
            # Remove user_id from response for security
            for record in records:
                record.pop("user_id", None)
                record["_id"] = str(record["_id"])
            
            return records
            
        except Exception as e:
            logger.error(f"Failed to retrieve medical records: {e}")
            return []

    async def get_medical_record(
        self,
        user_id: str,
        record_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a specific medical record by ID."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            record = await self.db.medical_records.find_one({
                "user_id": hashed_user_id,
                "_id": ObjectId(record_id)
            })
            
            if record:
                # Remove user_id from response for security
                record.pop("user_id", None)
                record["_id"] = str(record["_id"])
                return record
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve medical record {record_id}: {e}")
            return None

    async def update_medical_record(
        self,
        user_id: str,
        record_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """Update a specific medical record."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            # Add updated timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.db.medical_records.update_one(
                {"user_id": hashed_user_id, "_id": ObjectId(record_id)},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update medical record {record_id}: {e}")
            return False

    async def delete_medical_record(
        self,
        user_id: str,
        record_id: str
    ) -> bool:
        """Delete a specific medical record."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            result = await self.db.medical_records.delete_one({
                "user_id": hashed_user_id,
                "_id": ObjectId(record_id)
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Failed to delete medical record {record_id}: {e}")
            return False
    
    async def store_user_pii(self, user_id: str, pii_data: Dict[str, Any]) -> bool:
        """Store encrypted PII data for a user."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            # TODO: Implement AES-256 encryption for PII fields
            # For now, storing hashed version
            encrypted_pii = {
                "user_id": hashed_user_id,
                "encrypted_data": pii_data,  # Should be encrypted
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.db.user_pii.replace_one(
                {"user_id": hashed_user_id},
                encrypted_pii,
                upsert=True
            )
            
            logger.info(f"PII data stored for user {user_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store PII data: {e}")
            return False
    
    async def store_timeline_event(
        self,
        user_id: str,
        event_data: Dict[str, Any]
    ) -> str:
        """Store a timeline event for a user."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            event_id = str(ObjectId())  # Generate event ID first
            
            timeline_event = {
                "user_id": hashed_user_id,
                "event_id": event_id,
                "event_type": event_data.get("event_type", "general"),
                "title": event_data.get("title", ""),
                "description": event_data.get("description", ""),
                "timestamp": event_data.get("timestamp", datetime.utcnow()),
                "severity": event_data.get("severity", "medium"),
                "metadata": event_data.get("metadata", {}),
                "created_at": datetime.utcnow()
            }
            
            result = await self.db.timeline_events.insert_one(timeline_event)
            
            logger.info(f"Timeline event stored for user {user_id[:8]}...")
            return event_id  # Return the event_id, not the MongoDB ObjectId
            
        except Exception as e:
            logger.error(f"Failed to store timeline event: {e}")
            raise
    
    async def get_timeline_events(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieve timeline events for a user."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            cursor = self.db.timeline_events.find(
                {"user_id": hashed_user_id}
            ).sort("timestamp", -1).limit(limit)
            
            events = await cursor.to_list(length=limit)
            
            # Remove user_id from response
            for event in events:
                event.pop("user_id", None)
                event["_id"] = str(event["_id"])
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to retrieve timeline events: {e}")
            return []
    
    async def get_timeline_event(
        self,
        user_id: str,
        event_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a specific timeline event for a user."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            # Try finding by event_id field first, then by ObjectId
            event = await self.db.timeline_events.find_one({
                "user_id": hashed_user_id,
                "event_id": event_id
            })
            
            if not event:
                # Try finding by MongoDB ObjectId
                try:
                    event = await self.db.timeline_events.find_one({
                        "user_id": hashed_user_id,
                        "_id": ObjectId(event_id)
                    })
                except Exception:
                    pass  # Invalid ObjectId format
            
            if event:
                event.pop("user_id", None)
                event["_id"] = str(event["_id"])
                return event
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve timeline event: {e}")
            return None
    
    async def delete_timeline_event(
        self,
        user_id: str,
        event_id: str
    ) -> bool:
        """Delete a specific timeline event for a user."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            # Try deleting by event_id field first, then by ObjectId
            result = await self.db.timeline_events.delete_one({
                "user_id": hashed_user_id,
                "event_id": event_id
            })
            
            if result.deleted_count == 0:
                # Try deleting by MongoDB ObjectId
                try:
                    result = await self.db.timeline_events.delete_one({
                        "user_id": hashed_user_id,
                        "_id": ObjectId(event_id)
                    })
                except Exception:
                    pass  # Invalid ObjectId format
            
            logger.info(f"Timeline event deleted for user {user_id[:8]}...: {result.deleted_count > 0}")
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Failed to delete timeline event: {e}")
            return False

    async def store_document_metadata(
        self,
        user_id: str,
        filename: str,
        file_path: str,
        metadata: Dict[str, Any],
        document_id: Optional[str] = None  # Allow external document ID
    ) -> str:
        """Store document metadata for uploaded files."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            doc_metadata = {
                "user_id": hashed_user_id,
                "document_id": document_id or str(ObjectId()),  # Use provided ID or generate new one
                "filename": filename,
                "file_path": file_path,
                "metadata": metadata,
                "upload_timestamp": datetime.utcnow(),
                "processed": False,
                "processing_status": "pending"
            }
            
            result = await self.db.document_metadata.insert_one(doc_metadata)
            
            logger.info(f"Document metadata stored for {filename}")
            return document_id or str(result.inserted_id)  # Return provided ID or generated ID
            
        except Exception as e:
            logger.error(f"Failed to store document metadata: {e}")
            raise
    
    async def update_document_processing_status(
        self,
        document_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update document processing status."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            update_data = {
                "processing_status": status,
                "updated_at": datetime.utcnow()
            }
            
            if status == "completed":
                update_data["processed"] = True
            
            if metadata:
                update_data["metadata"] = metadata
            
            result = await self.db.document_metadata.update_one(
                {"document_id": document_id},  # Search by document_id field instead of _id
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update document status: {e}")
            return False
            logger.error(f"Failed to update document status: {e}")
            return False
    
    async def update_timeline_event(
        self,
        user_id: str,
        event_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """Update a specific timeline event for a user."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            # Add updated timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            # Try updating by event_id field first, then by ObjectId
            result = await self.db.timeline_events.update_one(
                {
                    "user_id": hashed_user_id,
                    "event_id": event_id
                },
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                # Try updating by MongoDB ObjectId
                try:
                    result = await self.db.timeline_events.update_one(
                        {
                            "user_id": hashed_user_id,
                            "_id": ObjectId(event_id)
                        },
                        {"$set": update_data}
                    )
                except Exception:
                    pass  # Invalid ObjectId format
            
            logger.info(f"Timeline event updated for user {user_id[:8]}...: {result.modified_count > 0}")
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Failed to update timeline event: {e}")
            return False

    async def store_clinical_record(
        self,
        clinical_record: Dict[str, Any]
    ) -> str:
        """Store a comprehensive clinical record."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            # Hash the patient_id for isolation
            patient_id = clinical_record["patient_id"]
            hashed_patient_id = self._hash_user_id(patient_id)
            
            # Prepare the clinical record for storage
            record = {
                "patient_id": hashed_patient_id,
                "original_patient_id": patient_id,  # Keep for reference (remove in production)
                "document_id": clinical_record["document_id"],
                "document_title": clinical_record["document_title"],
                "document_date": clinical_record["document_date"],
                "clinician": clinical_record["clinician"],
                "injuries": clinical_record["injuries"],
                "diagnoses": clinical_record["diagnoses"],
                "procedures": clinical_record["procedures"],
                "medications": clinical_record["medications"],
                "clinical_sections": clinical_record["clinical_sections"],
                "narrative_sections": clinical_record["narrative_sections"],
                "timeline": clinical_record["timeline"],
                "medical_codes": clinical_record["medical_codes"],
                "metadata": {
                    **clinical_record["metadata"],
                    "collection_type": "clinical_record",
                    "stored_at": datetime.utcnow().isoformat()
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Store in MongoDB
            result = await self.db.clinical_records.insert_one(record)
            
            logger.info(f"Clinical record stored for patient {patient_id[:8]}... with ID: {result.inserted_id}")
            return result.inserted_id
            
        except Exception as e:
            logger.error(f"Failed to store clinical record: {e}")
            raise
    
    async def get_clinical_records(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0,
        document_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get clinical records for a user."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            # Build query
            query = {"patient_id": hashed_user_id}
            if document_type:
                query["document_title"] = {"$regex": document_type, "$options": "i"}
            
            # Execute query
            cursor = self.db.clinical_records.find(query).sort("created_at", -1).skip(skip).limit(limit)
            records = await cursor.to_list(length=limit)
            
            # Remove hashed IDs from records
            for record in records:
                record["_id"] = str(record["_id"])
                record.pop("patient_id", None)  # Remove hashed ID
                record["patient_id"] = record.pop("original_patient_id", user_id)  # Restore original
            
            logger.info(f"Retrieved {len(records)} clinical records for user {user_id[:8]}...")
            return records
            
        except Exception as e:
            logger.error(f"Failed to get clinical records: {e}")
            return []

    async def get_clinical_record_by_document_id(
        self,
        user_id: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific clinical record by document ID."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            record = await self.db.clinical_records.find_one({
                "patient_id": hashed_user_id,
                "document_id": document_id
            })
            
            if record:
                record["_id"] = str(record["_id"])
                record.pop("patient_id", None)  # Remove hashed ID
                record["patient_id"] = record.pop("original_patient_id", user_id)  # Restore original
                
                logger.info(f"Retrieved clinical record {document_id} for user {user_id[:8]}...")
                return record
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get clinical record {document_id}: {e}")
            return None

    async def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def list_user_ids(self) -> List[str]:
        """List all user IDs that have data in MongoDB."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            # Get distinct user_ids from medical_records collection
            user_ids = await self.db.medical_records.distinct("user_id", {})
            logger.info(f"Found {len(user_ids)} users in MongoDB")
            return user_ids
            
        except Exception as e:
            logger.error(f"Failed to list user IDs: {e}")
            return []

    async def get_user_pii(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve PII data for a specific user."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            result = await self.db.user_pii.find_one({
                "user_id": hashed_user_id
            })
            
            if result:
                # Remove MongoDB _id from result
                result.pop("_id", None)
                return result
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user PII: {e}")
            return None

    async def list_user_document_metadata(self, user_id: str) -> List[Dict[str, Any]]:
        """List document metadata for a specific user."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            
            cursor = self.db.document_metadata.find({
                "user_id": hashed_user_id
            })
            
            documents = []
            async for doc in cursor:
                doc.pop("_id", None)  # Remove MongoDB _id
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to list user documents: {e}")
            return []

    async def delete_user_data(self, user_id: str) -> Dict[str, Any]:
        """Delete all data for a specific user from MongoDB."""
        if not self._initialized:
            raise RuntimeError("MongoDB not initialized")
        
        try:
            hashed_user_id = self._hash_user_id(user_id)
            deletion_results = {}
            
            # Delete from medical_records collection
            medical_records_result = await self.db.medical_records.delete_many({
                "user_id": hashed_user_id
            })
            deletion_results["medical_records"] = medical_records_result.deleted_count
            
            # Delete from timeline_events collection
            timeline_events_result = await self.db.timeline_events.delete_many({
                "user_id": hashed_user_id
            })
            deletion_results["timeline_events"] = timeline_events_result.deleted_count
            
            # Delete from document_metadata collection
            document_metadata_result = await self.db.document_metadata.delete_many({
                "user_id": hashed_user_id
            })
            deletion_results["document_metadata"] = document_metadata_result.deleted_count
            
            # Delete from user_pii collection
            user_pii_result = await self.db.user_pii.delete_one({
                "user_id": hashed_user_id
            })
            deletion_results["user_pii"] = user_pii_result.deleted_count
            
            # Delete from clinical_records collection if it exists
            try:
                clinical_records_result = await self.db.clinical_records.delete_many({
                    "user_id": hashed_user_id
                })
                deletion_results["clinical_records"] = clinical_records_result.deleted_count
            except Exception as e:
                logger.warning(f"Could not delete from clinical_records: {e}")
                deletion_results["clinical_records"] = 0
            
            total_deleted = sum(deletion_results.values())
            
            logger.info(f"Deleted MongoDB data for user {user_id[:8]}...: {deletion_results}")
            
            return {
                "success": total_deleted > 0,
                "total_deleted": total_deleted,
                "breakdown": deletion_results
            }
            
        except Exception as e:
            logger.error(f"Failed to delete user data from MongoDB: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_deleted": 0,
                "breakdown": {}
            }


# Global MongoDB instance
mongo_db = MongoDB()


async def init_mongo(mongo_uri: str, db_name: str = "digital_twin"):
    """Initialize global MongoDB instance."""
    await mongo_db.initialize(mongo_uri, db_name)


async def get_mongo() -> MongoDB:
    """Get MongoDB instance."""
    if not mongo_db._initialized:
        raise RuntimeError("MongoDB not initialized. Call init_mongo() first.")
    return mongo_db
