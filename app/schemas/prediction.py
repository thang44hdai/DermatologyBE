from pydantic import BaseModel
from typing import List, Optional


class PredictionItem(BaseModel):
    """Individual prediction item with label and confidence"""
    label_en: str
    label_vi: str
    confidence: float


class PredictionData(BaseModel):
    """Prediction data with all details"""
    label_en: str
    label_vi: str
    confidence: float
    all_predictions: List[PredictionItem]
    scan_id: int
    disease_id: int
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
