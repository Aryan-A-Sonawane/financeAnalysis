"""Configuration management for FinSightAI."""

from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "FinSightAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # API
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return v

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "finsight"
    POSTGRES_USER: str = "finsight_user"
    POSTGRES_PASSWORD: str
    DATABASE_URL: Optional[str] = None

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # NebulaGraph
    NEBULA_HOST: str = "localhost"
    NEBULA_PORT: int = 9669
    NEBULA_USER: str = "root"
    NEBULA_PASSWORD: str = "nebula"
    NEBULA_SPACE: str = "finsight"
    NEBULA_POOL_SIZE: int = 10

    # Weaviate
    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_API_KEY: str = ""
    WEAVIATE_TIMEOUT: int = 120

    # MinIO/S3
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "finsight-documents"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.1

    # OCR
    TESSERACT_PATH: str = "tesseract"
    TESSERACT_LANG: str = "eng"
    PADDLEOCR_LANG: str = "en"
    PADDLEOCR_USE_GPU: bool = False

    # Document Processing
    MAX_FILE_SIZE_MB: int = 50
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    MIN_CHUNK_SIZE: int = 100

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10

    # Observability
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "finsight-ai"
    LANGSMITH_TRACING: bool = False

    # Security
    HIPAA_MODE: bool = True
    ENCRYPTION_KEY: str = ""
    PASSWORD_MIN_LENGTH: int = 12

    # Workers
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Feature Flags
    ENABLE_FRAUD_DETECTION: bool = True
    ENABLE_GRAPH_REASONING: bool = True
    ENABLE_COMPLIANCE_CHECK: bool = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
