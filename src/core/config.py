"""
Configuration settings for Medical Digital Twin API
Uses environment variables with Pydantic validation
"""

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict, Any
import os
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="allow",  # allow unknown env vars to avoid validation errors
        env_file=".env",
        env_file_encoding="utf-8",
    )
    """Application settings with environment variable support"""
    
    # Project Info
    PROJECT_NAME: str = "Medical Digital Twin API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    PRODUCTION: bool = Field(default=False, env="PRODUCTION")
    
    # Security
    SECRET_KEY: str = Field("changeme", env="SECRET_KEY")
    
    # JWT Configuration (SYNCHRONIZED WITH BACKEND)
    JWT_SECRET_KEY: str = Field("your-secret-key", env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    JWT_REQUIRE_AUTH: bool = Field(True, env="JWT_REQUIRE_AUTH")
    
    # AgentOps Configuration
    AGENTOPS_API_KEY: Optional[str] = Field(None, env="AGENTOPS_API_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:5175",
            "http://127.0.0.1:5175",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "*"  # Allow all origins for development
        ],
        env="ALLOWED_ORIGINS"
    )
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    OPENAI_MODEL_COMPLEX: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL_COMPLEX")
    OPENAI_MODEL_SIMPLE: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL_SIMPLE")
    OPENAI_MAX_RETRIES: int = 3
    OPENAI_TIMEOUT: int = 30
    OPENAI_MAX_TOKENS: int = 4096
    
    # Rate Limiting (10 req/sec, 1000/hour)
    RATE_LIMIT_PER_SECOND: int = 10
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # MongoDB Configuration
    MONGO_URI: str = Field(
        default="mongodb://root:example@mongo:27017/medical_twin?authSource=admin",
        env="MONGO_URI"
    )
    MONGO_DATABASE: str = Field(default="medical_twin", env="MONGO_DATABASE")
    MONGO_DB_NAME: str = Field(default="medical_twin", env="MONGO_DB_NAME")  # Added for compatibility
    
    @validator('MONGO_DATABASE', pre=True)
    def set_mongo_database_from_db_name(cls, v, values):
        """Ensure MONGO_DATABASE uses MONGO_DB_NAME if set"""
        mongo_db_name = values.get('MONGO_DB_NAME')
        if mongo_db_name and mongo_db_name != v:
            return mongo_db_name
        return v
    
    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379/0", env="REDIS_URL")
    REDIS_QUEUE_KEY: str = "medical:document:queue"
    REDIS_RESULT_TTL: int = 3600 * 24  # 24 hours
    
    # Neo4j
    NEO4J_URI: str = Field(default="bolt://neo4j:7687", env="NEO4J_URI")
    NEO4J_USER: str = Field(default="neo4j", env="NEO4J_USER")  # Fixed: Changed from NEO4J_USERNAME to NEO4J_USER
    NEO4J_USERNAME: str = Field(default="neo4j", env="NEO4J_USERNAME")  # Keep for backward compatibility
    NEO4J_PASSWORD: str = Field(..., env="NEO4J_PASSWORD")
    
    # Milvus
    MILVUS_HOST: str = Field(default="milvus", env="MILVUS_HOST")
    MILVUS_PORT: int = Field(default=19530, env="MILVUS_PORT")
    MILVUS_COLLECTION_NAME: str = "medical_documents"
    MILVUS_DIM: int = 1536  # OpenAI embedding dimension
    
    # MinIO (S3-compatible storage)
    MINIO_ENDPOINT: str = Field(default="minio:9000", env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", env="MINIO_SECRET_KEY")
    MINIO_BUCKET: str = Field(default="medical-documents", env="MINIO_BUCKET")
    MINIO_SECURE: bool = Field(default=False, env="MINIO_SECURE")
    
    # File Processing
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_FILE_TYPES: List[str] = [
        ".pdf", ".jpg", ".jpeg", ".png", ".docx", ".txt", ".dicom", ".dcm"
    ]
    
    # Worker Configuration
    WORKER_CONCURRENCY: int = Field(default=5, env="WORKER_CONCURRENCY")
    WORKER_BATCH_SIZE: int = Field(default=10, env="WORKER_BATCH_SIZE")
    
    # LLM Processing Configuration
    LLM_CHUNK_SIZE: int = 2000  # Characters per chunk for LLM processing
    LLM_CHUNK_OVERLAP: int = 200
    LLM_TEMPERATURE: float = 0.1  # Low temperature for consistent extraction
    
    # Body Parts Configuration
    BODY_PARTS: List[str] = [
        # Head and Neck
        "brain", "eyes", "ears", "nose", "throat", "neck", "face", "skull",
        # Torso - Upper
        "shoulder_left", "shoulder_right", "chest", "heart", "lungs", "thyroid",
        # Torso - Mid
        "liver", "stomach", "pancreas", "spleen", "gallbladder",
        # Torso - Lower
        "kidneys", "bladder", "intestines_small", "intestines_large", "appendix",
        # Reproductive
        "reproductive_system",
        # Musculoskeletal
        "spine", "ribs", "pelvis", "hip_left", "hip_right",
        # Extremities
        "arm_left", "arm_right", "leg_left", "leg_right",
        "hand_left", "hand_right", "foot_left", "foot_right",
        # Systems
        "blood", "immune_system", "nervous_system", "lymphatic_system", "skin"
    ]
    
    # Severity Levels
    SEVERITY_LEVELS: Dict[str, Dict[str, Any]] = {
        "normal": {"min": 0, "max": 2, "color": "#00FF00"},
        "mild": {"min": 2, "max": 4, "color": "#FFFF00"},
        "moderate": {"min": 4, "max": 6, "color": "#FFA500"},
        "severe": {"min": 6, "max": 8, "color": "#FF4444"},
        "critical": {"min": 8, "max": 10, "color": "#8B0000"}
    }
    
    # Patient ID Configuration
    PATIENT_ID_SALT: str = Field(default="medical-twin-salt-2024", env="PATIENT_ID_SALT")
    
    # Debug Configuration
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    REPORTS_DIR: Path = BASE_DIR / "data" / "reports"
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_origins(cls, v):
        """Parse comma-separated origins"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("UPLOAD_DIR", "PROCESSED_DIR", "REPORTS_DIR")
    def create_directories(cls, v):
        """Create directories if they don't exist"""
        v.mkdir(parents=True, exist_ok=True)
        return v
    


# Create settings instance
settings = Settings()

# Prompt templates for LLM extraction
EXTRACTION_PROMPTS = {
    "medical_entities": """
You are a medical information extraction specialist. Extract the following from the medical document:

1. Medical Conditions/Diagnoses
2. Symptoms
3. Treatments/Procedures
4. Medications
5. Test Results
6. Body Parts Affected
7. Severity Indicators
8. Dates and Timeline Events

For each extracted item, provide:
- Category (condition/symptom/treatment/medication/test_result)
- Text (exact or normalized medical term)
- Body Parts (from this list: {body_parts})
- Severity (0-10 scale, null if not applicable)
- Date (if mentioned)
- Confidence (0-1)

Return as JSON array.

Document Text:
{text}
""",
    
    "body_part_mapping": """
Map the following medical information to the most relevant body parts from this list:
{body_parts}

Medical Information:
{medical_info}

Consider anatomical relationships and medical knowledge. Return a JSON object with:
- primary_body_parts: List of directly affected body parts
- secondary_body_parts: List of indirectly affected body parts
- confidence: 0-1 score
""",
    
    "severity_assessment": """
Assess the severity of the following medical condition on a 0-10 scale:
0-2: Normal/Resolved
2-4: Mild
4-6: Moderate
6-8: Severe
8-10: Critical/Life-threatening

Condition: {condition}
Context: {context}

Return JSON with:
- severity_score: 0-10
- severity_level: normal/mild/moderate/severe/critical
- factors: List of factors influencing the score
- confidence: 0-1
""",
    
    "timeline_extraction": """
Extract all temporal information and create a medical timeline from this text.
Include dates, durations, sequences of events, and relative time references.

Text: {text}

Return JSON array of timeline events with:
- date: ISO format or relative description
- event_type: diagnosis/treatment/symptom/test/follow_up
- description: Brief description
- duration: If applicable
- sequence_order: If events are related
"""
}

# Expert agent specialties
EXPERT_SPECIALTIES = {
    "cardiologist": ["heart", "blood", "circulatory_system"],
    "neurologist": ["brain", "nervous_system", "spine"],
    "pulmonologist": ["lungs", "respiratory_system", "chest"],
    "gastroenterologist": ["stomach", "intestines_small", "intestines_large", "liver", "pancreas"],
    "orthopedist": ["bones", "joints", "spine", "musculoskeletal"],
    "endocrinologist": ["thyroid", "pancreas", "endocrine_system"],
    "nephrologist": ["kidneys", "bladder", "urinary_system"],
    "dermatologist": ["skin"],
    "hematologist": ["blood", "immune_system", "lymphatic_system"],
    "internist": ["general", "systemic"]
}
