"""
Centralised app configuration using Pydantic v2 BaseSettings.

All variables can be overridden in `.env`.
"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, RedisDsn, PostgresDsn, ValidationError

ENV_FILE = Path(".env")


class Settings(BaseSettings):
    # ── OpenAI ───────────────────────────────────────────────────────────────
    openai_api_key: str = Field(..., validation_alias="openai_api_key")
    openai_model_chat: str = Field("gpt-4o-mini", validation_alias="openai_model_chat")
    openai_model_search: str = Field(
        "gpt-4o-mini-search-preview", validation_alias="openai_model_search"
    )

    # ── MongoDB ──────────────────────────────────────────────────────────────
    mongo_uri: str = Field("mongodb://mongo:27017", validation_alias="mongo_uri")
    mongo_db_name: str = Field("digital_twin", validation_alias="mongo_db_name")
    mongo_initdb_root_username: str = Field(..., validation_alias="mongo_initdb_root_username")
    mongo_initdb_root_password: str = Field(..., validation_alias="mongo_initdb_root_password")

    # ── Redis ────────────────────────────────────────────────────────────────
    redis_url: RedisDsn = Field("redis://redis:6379/0", validation_alias="redis_url")
    redis_host: str = Field(..., validation_alias="redis_host")
    redis_port: int = Field(..., validation_alias="redis_port")

    # ── Neo4j ────────────────────────────────────────────────────────────────
    neo4j_uri: str = Field("bolt://neo4j:7687", validation_alias="neo4j_uri")
    neo4j_user: str = Field("neo4j", validation_alias="neo4j_user")
    neo4j_password: str = Field(..., validation_alias="neo4j_password")

    # ── Milvus ───────────────────────────────────────────────────────────────
    milvus_host: str = Field("milvus", validation_alias="milvus_host")
    milvus_port: int = Field(19530, validation_alias="milvus_port")
    milvus_collection: str = Field("medical_knowledge", validation_alias="milvus_collection")
    milvus_uri: str = Field(..., validation_alias="milvus_uri")

    # ── AgentOps ─────────────────────────────────────────────────────────────
    agentops_api_key: Optional[str] = Field(None, validation_alias="agentops_api_key")

    # ── JWT Authentication ──────────────────────────────────────────────────
    jwt_secret_key: str = Field(..., validation_alias="jwt_secret_key")
    jwt_refresh_secret_key: Optional[str] = Field(None, validation_alias="jwt_refresh_secret_key")
    jwt_algorithm: str = Field("HS256", validation_alias="jwt_algorithm")
    access_token_expire_minutes: int = Field(15, validation_alias="access_token_expire_minutes")
    refresh_token_expire_days: int = Field(7, validation_alias="refresh_token_expire_days")
    jwt_require_auth: bool = Field(False, validation_alias="jwt_require_auth")

    # ── Encryption ───────────────────────────────────────────────────────────
    aes_encryption_key: str = Field(..., validation_alias="aes_encryption_key")
    patient_id_salt: str = Field(..., validation_alias="patient_id_salt")

    # ── Misc ─────────────────────────────────────────────────────────────────
    debug: bool = Field(False, validation_alias="debug")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


try:
    settings = Settings()  # single instance for whole app
except ValidationError as exc:
    raise SystemExit(f"❌  Invalid configuration in .env:\n{exc}") from exc
