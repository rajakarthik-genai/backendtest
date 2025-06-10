"""
Centralised app configuration using Pydantic v2 BaseSettings.

All variables can be overridden in `.env`.
"""

from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field, AliasChoices, RedisDsn, PostgresDsn, ValidationError

ENV_FILE = Path(".env")


class Settings(BaseSettings):
    # ── OpenAI ───────────────────────────────────────────────────────────────
    openai_api_key: str = Field(..., validation_alias=AliasChoices("OPENAI_API_KEY"))
    openai_model_chat: str = Field("gpt-4o-mini", validation_alias="OPENAI_MODEL_CHAT")
    openai_model_search: str = Field(
        "gpt-4o-mini-search-preview", validation_alias="OPENAI_MODEL_SEARCH"
    )

    # ── MongoDB ──────────────────────────────────────────────────────────────
    mongo_uri: str = Field("mongodb://mongo:27017", validation_alias="MONGO_URI")
    mongo_db_name: str = Field("digital_twin", validation_alias="MONGO_DB_NAME")

    # ── Redis ────────────────────────────────────────────────────────────────
    redis_url: RedisDsn = Field("redis://redis:6379/0", validation_alias="REDIS_URL")

    # ── Neo4j ────────────────────────────────────────────────────────────────
    neo4j_uri: str = Field("bolt://neo4j:7687", validation_alias="NEO4J_URI")
    neo4j_user: str = Field("neo4j", validation_alias="NEO4J_USER")
    neo4j_password: str = Field(..., validation_alias=AliasChoices("NEO4J_PASSWORD"))

    # ── Milvus ───────────────────────────────────────────────────────────────
    milvus_host: str = Field("milvus", validation_alias="MILVUS_HOST")
    milvus_port: int = Field(19530, validation_alias="MILVUS_PORT")
    milvus_collection: str = Field("medical_knowledge", validation_alias="MILVUS_COLLECTION")

    # ── AgentOps ─────────────────────────────────────────────────────────────
    agentops_api_key: Optional[str] = Field(None, validation_alias="AGENTOPS_API_KEY")

    # ── Misc ─────────────────────────────────────────────────────────────────
    debug: bool = Field(False, validation_alias=AliasChoices("DEBUG"))

    model_config = {
        "env_file": ENV_FILE,
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


try:
    settings = Settings()  # single instance for whole app
except ValidationError as exc:
    raise SystemExit(f"❌  Invalid configuration in .env:\n{exc}") from exc
