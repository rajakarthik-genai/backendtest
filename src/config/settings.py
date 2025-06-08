from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Database and service URIs
    NEO4J_URI: str = Field(...)
    NEO4J_USER: str = Field(...)
    NEO4J_PASSWORD: str = Field(...)
    MILVUS_URI: str = Field(...)
    REDIS_HOST: str = Field(...)
    REDIS_PORT: int = Field(...)
    MONGO_INITDB_ROOT_USERNAME: str = Field(...)
    MONGO_INITDB_ROOT_PASSWORD: str = Field(...)
    MONGO_URI: str = Field(...)

    # OpenAI
    OPENAI_API_KEY: str = Field(...)
    OPENAI_CHAT_MODEL: str = Field(...)
    OPENAI_SEARCH_MODEL: str = Field(...)

    # AgentOps (optional, if used)
    AGENTOPS_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()