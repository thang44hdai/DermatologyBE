from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, Union
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
    CORS_ORIGINS: Union[list, str] = ["*"]
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(',')]
        return v
    
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
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Refresh token expires in 7 days
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp', '.jfif'}
    
    # Upload directories
    UPLOAD_DIR: str = "uploads"
    DISEASE_IMAGES_DIR: str = "uploads/diseases"
    MEDICINE_IMAGES_DIR: str = "uploads/medicines"
    SCAN_IMAGES_DIR: str = "uploads/scans"
    
    # Firebase Storage
    FIREBASE_SERVICE_ACCOUNT_KEY: str = "firebase-service-account.json"
    FIREBASE_STORAGE_BUCKET: str = "learningapp-5ef0e.com"
    USE_FIREBASE_STORAGE: bool = False  # Set to True to use Firebase Storage instead of local storage
    
    # LLM Server Configuration (for RAG Chatbot)
    LLM_SERVER_URL: str = "http://localhost:8080/v1"
    
    # Vector Database (FAISS)
    FAISS_INDEX_PATH: str = "faiss_index_store"
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    # WebSocket Configuration
    WS_HEARTBEAT_INTERVAL: int = 30  # Heartbeat ping interval in seconds
    WS_CONNECTION_TIMEOUT: int = 60  # Connection timeout in seconds
    WS_MAX_CONNECTIONS_PER_USER: int = 3  # Maximum concurrent connections per user
    WS_RATE_LIMIT_MESSAGES_PER_MINUTE: int = 20  # Rate limit: messages per minute per user
    WS_RATE_LIMIT_BURST_SIZE: int = 5  # Rate limit: burst allowance (extra tokens)
    
    # Notification & Reminder Configuration
    NOTIFICATION_TIMEZONE: str = "Asia/Ho_Chi_Minh"  # UTC+7
    REMINDER_CHECK_INTERVAL: int = 60  # Check reminders every 60 seconds
    
    # OAuth2 Configuration
    GOOGLE_CLIENT_ID: str = ""  # Google OAuth client ID for Android
    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
