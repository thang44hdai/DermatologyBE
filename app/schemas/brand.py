from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BrandBase(BaseModel):
    """Base brand schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Brand name")
    description: Optional[str] = Field(None, description="Brand description")
    logo_path: Optional[str] = Field(None, description="Logo image path")


class BrandCreate(BrandBase):
    """Schema for creating a brand"""
    pass


class BrandUpdate(BaseModel):
    """Schema for updating a brand"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    logo_path: Optional[str] = None


class BrandResponse(BrandBase):
    """Response schema for brand"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class BrandListResponse(BaseModel):
    """Response schema for list of brands"""
    brands: list[BrandResponse]
    total: int
    skip: int
    limit: int


class BrandInfo(BaseModel):
    """Basic brand info for nested responses"""
    id: int
    name: str
    logo_path: Optional[str] = None


class MedicineInBrand(BaseModel):
    """Medicine info in brand listing"""
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


class BrandMedicinesResponse(BaseModel):
    """Response for getting medicines by brand"""
    brand: BrandInfo
    medicines: List[MedicineInBrand]
    total: int
    skip: int
    limit: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "brand": {
                    "id": 1,
                    "name": "Sanofi",
                    "logo_path": "https://storage.googleapis.com/sanofi_logo.jpg"
                },
                "medicines": [
                    {
                        "id": 1,
                        "name": "Doliprane 500mg",
                        "description": "Thuốc hạ sốt, giảm đau",
                        "generic_name": "Paracetamol",
                        "type": "tablet",
                        "dosage": "500mg",
                        "price": 35000,
                        "images": ["https://storage.googleapis.com/medicine1.jpg"]
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 50
            }
        }

