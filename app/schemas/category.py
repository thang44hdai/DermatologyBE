from pydantic import BaseModel, Field
from typing import Optional
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
