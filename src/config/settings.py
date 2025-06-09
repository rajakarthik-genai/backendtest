from pathlib import Path
from typing import Literal

from pydantic import (
    BaseSettings,
    Field,
    PostgresDsn,
    RedisDsn,
    ValidationError,
    field_validator,
)

ENV_FILE = Path(".env")


class Settings(BaseSettings):
    """Central settings object – loaded once then imported everywhere."""

    # ───────── OpenAI ────────────────────────────────────────────────────────
    openai_api_key: str = Field(..., validation_alias=AliasChoices("OPENAI_API_KEY"))
    openai_model_chat: str = Field(
        default="gpt-4o-mini", validation_alias=AliasChoices("OPENAI_MODEL_CHAT")
    )
    openai_model_search: str = Field(
        default="gpt-4o-mini-search-preview",
        validation_alias=AliasChoices("OPENAI_MODEL_SEARCH"),
    )

    # ───────── Databases ─────────────────────────────────────────────────────
    mongo_uri: str = Field(
        default="mongodb://mongo:27017", validation_alias=AliasChoices("MONGO_URI")
    )
    mongo_db_name: str = Field(
        default="digital_twin", validation_alias=AliasChoices("MONGO_DB_NAME")
    )

    redis_url: RedisDsn = Field(
        default="redis://redis:6379/0", validation_alias=AliasChoices("REDIS_URL")
    )

    neo4j_uri: str = Field(default="bolt://neo4j:7687", validation_alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", validation_alias="NEO4J_USER")
    neo4j_password: str = Field(..., validation_alias=AliasChoices("NEO4J_PASSWORD"))

    milvus_host: str = Field(default="milvus", validation_alias="MILVUS_HOST")
    milvus_port: int = Field(default=19530, validation_alias="MILVUS_PORT")

    # ───────── Misc / Ops ────────────────────────────────────────────────────
    agentops_api_key: str | None = Field(
        default=None, validation_alias=AliasChoices("AGENTOPS_API_KEY")
    )
    debug: bool = Field(False, validation_alias=AliasChoices("DEBUG"))

    model_config = {
        "env_file": ENV_FILE,
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "case_sensitive": False,
    }

    # Example validator – ensure port is positive
    @field_validator("milvus_port")
    @classmethod
    def _positive_port(cls, v: int):
        if v <= 0:
            raise ValueError("milvus_port must be positive")
        return v


try:
    settings = Settings()  # imported by every module
except ValidationError as exc:
    raise SystemExit(f"❌ ENV configuration invalid:\n{exc}") from exc
