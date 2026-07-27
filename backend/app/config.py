"""
@spec DEPLOY-ENV-001
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    database_url: str = "postgresql://postgres:postgres@localhost:5432/qassist"

    aws_region: str = "us-east-1"
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None

    bedrock_claude_model_id: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    bedrock_embed_model_id: str = "amazon.titan-embed-text-v2:0"
    bedrock_embed_dimension: int = 1024

    frontend_origin: str = "http://localhost:5173"

    max_upload_bytes: int = 10 * 1024 * 1024
    chunk_size_chars: int = 500
    chunk_overlap_chars: int = 100
    default_top_k: int = 5
    max_tool_use_rounds: int = 4

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
