"""
Configuration settings for the Policy Summarizer backend.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/policy_summarizer"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # File Storage
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 25
    allowed_extensions: list[str] = [".pdf", ".txt", ".html", ".jpg", ".jpeg", ".png"]
    
    # NLP Models (CPU-optimized)
    summarization_model: str = "sshleifer/distilbart-cnn-12-6"
    ner_model: str = "en_core_web_sm"
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # CORS
    cors_origins: list[str] = ["http://localhost:8501", "http://localhost:3000"]
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Create uploads directory if it doesn't exist
settings = get_settings()
os.makedirs(settings.upload_dir, exist_ok=True)
