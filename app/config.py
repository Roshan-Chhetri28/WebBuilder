from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str
    
    # Database Configuration
    database_url: str = "postgresql://placeholder:placeholder@localhost:5432/placeholder"
    
    # FastAPI Configuration
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Application Configuration
    app_name: str = "Menu2Site AI"
    app_version: str = "0.1.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields in .env


# Global settings instance
settings = Settings()
