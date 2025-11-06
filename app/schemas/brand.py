from pydantic import BaseModel, Field
from typing import Optional
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
