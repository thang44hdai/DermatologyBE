from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class PredictionItem(BaseModel):
    """Individual prediction item with label and confidence"""
    label_en: str
    label_vi: str
    confidence: float


class DiseaseInfo(BaseModel):
    """Disease information model"""
    id: int
    disease_name: str
    description: Optional[str]
    symptoms: Optional[str]
    treatment: Optional[str]
    image_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PredictionData(BaseModel):
    """Prediction data with all details"""
    label_en: str
    label_vi: str
    confidence: float
    scan_id: int
    disease: DiseaseInfo
    diagnosis_history_id: int
    user_id: int


class PredictionResponse(BaseModel):
    """Response model for disease prediction"""
    success: bool
    data: PredictionData


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    model_loaded: bool
    device: str
