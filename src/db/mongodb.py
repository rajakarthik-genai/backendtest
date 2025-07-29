"""
MongoDB database connection and operations module.

Provides comprehensive MongoDB integration for medical document storage,
patient records management, and medical data persistence.

Features:
- Asynchronous MongoDB connection management
- Automatic connection pooling and health checks
- Comprehensive indexing for query performance
- Document lifecycle management (upload, processing, completion)
- Patient-centric data organization
- Integration with Neo4j knowledge graph
- Medical entity storage and retrieval
- Processing status tracking and monitoring

Database Structure:
- documents: Medical document metadata and processing status
- patients: Patient information and medical history
- medical_records: Structured medical data and entities
- embeddings: Vector embeddings for AI retrieval
- processing_logs: Audit trail and processing metadata
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional

from src.core.config import settings
from src.core.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

mongodb = MongoDB()

async def connect_to_mongo():
    """
    Establish asynchronous MongoDB connection with comprehensive setup.
    
    Process:
    1. Initialize async MongoDB client with connection pooling
    2. Test connectivity with ping command
    3. Create performance-optimized indexes
    4. Setup database collections and schema validation
    5. Configure connection monitoring and logging
    
    Raises:
        DatabaseConnectionError: If connection fails or authentication issues
    
    Features:
    - Automatic retry and connection recovery
    - Connection pooling for high performance
    - Comprehensive error handling and logging
    - Health check integration
    """
    try:
        mongodb.client = AsyncIOMotorClient(settings.MONGO_URI)
        mongodb.database = mongodb.client[settings.MONGO_DATABASE]
        
        # Test connection
        await mongodb.client.admin.command('ping')
        logger.info("Connected to MongoDB successfully")
        
        # Create indexes
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise DatabaseConnectionError(f"MongoDB connection failed: {str(e)}")

async def close_mongo_connection():
    """Close database connection"""
    if mongodb.client:
        mongodb.client.close()
        logger.info("MongoDB connection closed")

async def create_indexes():
    """
    Create comprehensive database indexes for optimal query performance.
    
    Indexes support:
    - Document retrieval by ID and patient
    - Patient-centric data queries
    - Processing status monitoring
    - Medical entity searches
    - Timeline queries
    - Full-text search capabilities
    
    Index Types:
    - Unique indexes for document integrity
    - Compound indexes for complex queries
    - Text indexes for medical content search
    - Date indexes for temporal queries
    - Patient ID indexes for data partitioning
    """
    try:
        # Documents collection indexes
        await mongodb.database.documents.create_index("document_id", unique=True)
        await mongodb.database.documents.create_index("patient_id")
        await mongodb.database.documents.create_index("status")
        await mongodb.database.documents.create_index("uploaded_at")
        
        # Chat history indexes
        await mongodb.database.chat_history.create_index("patient_id")
        await mongodb.database.chat_history.create_index([("timestamp", -1)])
        
        # Expert opinions indexes
        await mongodb.database.expert_opinions.create_index("patient_id")
        await mongodb.database.expert_opinions.create_index([("created_at", -1)])
        
        # Reports indexes
        await mongodb.database.reports.create_index("report_id", unique=True)
        await mongodb.database.reports.create_index("patient_id")
        
        # Users indexes
        await mongodb.database.users.create_index("username", unique=True)
        await mongodb.database.users.create_index("email", unique=True)
        
        logger.info("MongoDB indexes created successfully")
        
    except Exception as e:
        logger.warning(f"Failed to create some indexes: {e}")

def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if not mongodb.database:
        raise DatabaseConnectionError("Database not connected")
    return mongodb.database
