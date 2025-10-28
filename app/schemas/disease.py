from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DiseaseBase(BaseModel):
    """Base disease schema"""
    disease_name: str = Field(..., min_length=1, max_length=255, description="Disease name")
    description: Optional[str] = Field(None, description="Disease description")
    treatment: Optional[str] = Field(None, description="Treatment information")
    image_url: Optional[str] = Field(None, max_length=255, description="Disease image URL")


class DiseaseCreate(DiseaseBase):
    """Schema for creating a disease"""
    pass


class DiseaseUpdate(BaseModel):
    """Schema for updating a disease"""
    disease_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    treatment: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=255)


class DiseaseResponse(DiseaseBase):
    """Response schema for disease"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DiseaseListResponse(BaseModel):
    """Response schema for list of diseases"""
    diseases: list[DiseaseResponse]
    total: int
    skip: int
    limit: int


class DiseaseDetailResponse(DiseaseResponse):
    """Detailed disease response with related info counts"""
    symptoms_count: int = Field(..., description="Number of symptoms")
    medicines_count: int = Field(..., description="Number of medicines")
    diagnosis_count: int = Field(..., description="Number of diagnoses")
    
    class Config:
        from_attributes = True
