from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DiseaseBase(BaseModel):
    """Base disease schema"""
    disease_name: str = Field(..., min_length=1, max_length=255, description="Disease name")
    description: Optional[str] = Field(None, description="Disease description")
    symptoms: Optional[str] = Field(None, description="Disease symptoms")
    treatment: Optional[str] = Field(None, description="Treatment information")
    image_url: Optional[str] = Field(None, max_length=255, description="Disease image URL")


class DiseaseCreate(DiseaseBase):
    """Schema for creating a disease"""
    pass


class DiseaseUpdate(BaseModel):
    """Schema for updating a disease"""
    disease_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    symptoms: Optional[str] = None
    treatment: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=255)


class DiseaseResponse(DiseaseBase):
    """Response schema for disease"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class MedicineInfo(BaseModel):
    """Basic medicine info for disease response"""
    id: int
    name: str
    generic_name: Optional[str] = None
    type: Optional[str] = None
    price: Optional[int] = None
    image_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class DiseaseDetailResponse(DiseaseResponse):
    """Detailed disease response with related info counts"""
    medicines_count: int = Field(..., description="Number of medicines")
    diagnosis_count: int = Field(..., description="Number of diagnoses")
    medicines: List[MedicineInfo] = Field(default_factory=list, description="List of medicines for this disease")
    
    class Config:
        from_attributes = True


class DiseaseListResponse(BaseModel):
    """Response schema for list of diseases"""
    diseases: list[DiseaseDetailResponse]
    total: int
    skip: int
    limit: int


# Update forward references
DiseaseDetailResponse.model_rebuild()
