"""
Core configuration and settings for Struct-Recipt-Intilligent
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # App settings
    app_name: str = "Struct-Recipt-Intilligent API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database settings
    database_url: str = "postgresql://postgres:password@localhost:5432/structured_data_db"
    
    # API settings
    api_v1_prefix: str = "/api/v1"
    
    # CORS settings
    allowed_origins: list = ["*"]
    
    # Groq API settings
    groq_api_key: str = "your-groq-api-key-here"
    
    class Config:
        env_file = ".env"


settings = Settings()
