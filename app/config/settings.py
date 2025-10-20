from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # App Info
    APP_NAME: str = "Skin Disease Classification API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "API for classifying skin diseases using Fusion Model"
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # AI Model
    MODEL_PATH: str = "resources/models/skin_disease_model.pth"
    IMG_SIZE: int = 224
    
    # Database (SQLite for development, PostgreSQL for production)
    DATABASE_URL: str = "sqlite:///./dermatology.db"
    # For PostgreSQL: postgresql://user:password@localhost/dbname
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp', '.jfif'}
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
