from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class PredictionItem(BaseModel):
    """Individual prediction item with label and confidence"""
    label_en: str
    label_vi: str
    confidence: float


class MedicineInfo(BaseModel):
    """Medicine information for disease treatment"""
    id: int
    name: str
    description: Optional[str]
    generic_name: Optional[str]
    type: Optional[str]
    dosage: Optional[str]
    side_effects: Optional[str]
    suitable_for: Optional[str]
    price: Optional[int]
    images: Optional[List[str]]  # Parsed from JSON
    
    class Config:
        from_attributes = True


class DiseaseInfo(BaseModel):
    """Disease information model"""
    id: int
    disease_name: str
    description: Optional[str]
    symptoms: Optional[str]
    treatment: Optional[str]
    image_url: Optional[str]
    medicines: List[MedicineInfo] = []  # Added medicines list
    created_at: datetime
    
    class Config:
        from_attributes = True


class PredictionData(BaseModel):
    """Prediction data with all details"""
    label_en: str
    label_vi: str
    confidence: float
    scan_id: int
    image_url: str
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


class DiagnosisHistoryInfo(BaseModel):
    """Diagnosis history information"""
    id: int
    note: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ScanHistoryItem(BaseModel):
    """Individual scan history item"""
    scan_id: int
    image_url: Optional[str]
    scan_date: datetime
    status: str
    disease: Optional[DiseaseInfo]
    diagnosis_history: Optional[DiagnosisHistoryInfo]


class ScanHistoryResponse(BaseModel):
    """Response model for scan history list"""
    total: int
    skip: int
    limit: int
    scans: List[ScanHistoryItem]


class ScanDetailResponse(BaseModel):
    """Response model for scan detail"""
    scan_id: int
    user_id: int
    image_url: Optional[str]
    scan_date: datetime
    status: str
    disease: Optional[DiseaseInfo]
    diagnosis_history: Optional[DiagnosisHistoryInfo]
