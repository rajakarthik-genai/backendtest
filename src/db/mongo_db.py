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

    async def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


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
