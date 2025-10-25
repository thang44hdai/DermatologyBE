from pydantic import BaseModel
from typing import List, Optional


class PredictionItem(BaseModel):
    """Individual prediction item with label and confidence"""
    label_en: str
    label_vi: str
    confidence: float


class PredictionResponse(BaseModel):
    """Response model for disease prediction"""
    success: bool
    label_en: str
    label_vi: str
    confidence: float
    all_predictions: List[PredictionItem]
    scan_id: Optional[int] = None
    diagnosis_id: Optional[int] = None
    user_id: Optional[int] = None


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    model_loaded: bool
    device: str
