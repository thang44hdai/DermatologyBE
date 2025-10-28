from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PharmacyBase(BaseModel):
    """Base pharmacy schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Pharmacy name")
    address: str = Field(..., min_length=1, max_length=255, description="Pharmacy address")
    phone: Optional[str] = Field(None, max_length=50, description="Contact phone number")
    open_hours: Optional[str] = Field(None, max_length=100, description="Opening hours (e.g., '8:00-20:00')")
    ratings: Optional[float] = Field(None, ge=0, le=5, description="Pharmacy rating (0-5)")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")


class PharmacyCreate(PharmacyBase):
    """Schema for creating a pharmacy"""
    pass


class PharmacyUpdate(BaseModel):
    """Schema for updating a pharmacy"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    open_hours: Optional[str] = Field(None, max_length=100)
    ratings: Optional[float] = Field(None, ge=0, le=5)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PharmacyResponse(PharmacyBase):
    """Response schema for pharmacy"""
    id: int
    
    class Config:
        from_attributes = True


class PharmacyWithDistanceResponse(PharmacyResponse):
    """Response schema for pharmacy with distance"""
    distance_km: float = Field(..., description="Distance from user location in kilometers")
    
    class Config:
        from_attributes = True


class PharmacyListResponse(BaseModel):
    """Response schema for list of pharmacies"""
    pharmacies: list[PharmacyResponse]
    total: int
    skip: int
    limit: int
