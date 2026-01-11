from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    is_active: Optional[bool] = True


class CategoryCreate(CategoryBase):
    """Schema for creating a category"""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    """Schema for category response"""
    id: int
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    medicine_count: Optional[int] = Field(None, description="Number of medicines in this category")
    
    class Config:
        from_attributes = True


class CategoryInfo(BaseModel):
    """Basic category info for nested responses"""
    id: int
    name: str
    image_url: Optional[str] = None


class MedicineInCategory(BaseModel):
    """Medicine info in category listing"""
    id: int
    name: str
    description: str
    generic_name: Optional[str] = None
    type: Optional[str] = None
    dosage: Optional[str] = None
    price: Optional[float] = None
    images: Optional[List[str]] = []
    
    class Config:
        from_attributes = True


class CategoryMedicinesResponse(BaseModel):
    """Response for getting medicines by category"""
    category: CategoryInfo
    medicines: List[MedicineInCategory]
    total: int
    skip: int
    limit: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "category": {
                    "id": 1,
                    "name": "Thuốc giảm đau",
                    "image_url": "https://storage.googleapis.com/example.jpg"
                },
                "medicines": [
                    {
                        "id": 1,
                        "name": "Paracetamol 500mg",
                        "description": "Thuốc hạ sốt, giảm đau",
                        "generic_name": "Paracetamol",
                        "type": "tablet",
                        "dosage": "500mg",
                        "price": 25000,
                        "images": ["https://storage.googleapis.com/medicine1.jpg"]
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 50
            }
        }

