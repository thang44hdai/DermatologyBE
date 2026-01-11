from fastapi import APIRouter
from app.schemas.prediction import HealthResponse
from app.services.ai_service import ai_service

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns API status and model loading state
    """
    return {
        "status": "running",
        "model_loaded": ai_service.model_loaded,
        "device": str(ai_service.device)
    }


@router.get("/health", response_model=HealthResponse)
async def health():
    """Alternative health check endpoint"""
    return {
        "status": "running",
        "model_loaded": ai_service.model_loaded,
        "device": str(ai_service.device)
    }
