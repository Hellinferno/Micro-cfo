"""
MicroCFO Backend Configuration
Centralized settings management using Pydantic
"""

from typing import Optional, List
from functools import lru_cache
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # App Info
    APP_NAME: str = "MicroCFO"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")

    # API Settings
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./microcfo.db"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"

    # AI/LLM Settings
    GEMINI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # External Services
    REDIS_URL: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",  # Allow extra env variables
        "populate_by_name": True,  # Allow field population by alias or field name
    }

    @model_validator(mode='after')
    def check_secret_key(self) -> 'Settings':
        """Validate SECRET_KEY in production"""
        if not self.DEBUG and self.SECRET_KEY == "your-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be set in production environment")
        return self


@lru_cache(maxsize=1)  # Singleton pattern - one settings instance
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()
