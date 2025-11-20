from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os
from pathlib import Path

from app.config import settings
from app.api.v1.router import api_router
from app.services.ai_service import ai_service
from app.services.chat_service import chat_service
from app.db.session import engine
from app.models.database import Base

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create upload directories if not exist
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.DISEASE_IMAGES_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.MEDICINE_IMAGES_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.SCAN_IMAGES_DIR).mkdir(parents=True, exist_ok=True)

# ==========================================
# FASTAPI APP
# ==========================================

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# STARTUP/SHUTDOWN EVENTS
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting up application...")
    
    # Load AI model for skin disease prediction
    try:
        ai_service.load_model()
        logger.info("AI model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load AI model: {e}")
        logger.warning("Application will start but predictions will not work")
    
    # Initialize Chat Service (RAG with FAISS + LLM)
    try:
        chat_service.initialize()
        logger.info("Chat service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize chat service: {e}")
        logger.warning("Application will start but chat functionality will not work")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application...")

# ==========================================
# INCLUDE ROUTERS
# ==========================================

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Mount static files for serving uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ==========================================
# RUN SERVER
# ==========================================

if __name__ == "__main__":
    import uvicorn
    import sys
    import os
    
    # Add project root to Python path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Change to project root directory
    os.chdir(project_root)
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
