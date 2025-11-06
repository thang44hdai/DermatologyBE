from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, time


class PharmacyBase(BaseModel):
    """Base pharmacy schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Pharmacy name")
    address: str = Field(..., min_length=1, max_length=255, description="Pharmacy address")
    phone: Optional[str] = Field(None, max_length=50, description="Contact phone number")
    open_time: Optional[time] = Field(None, description="Opening time (e.g., 08:00:00)")
    close_time: Optional[time] = Field(None, description="Closing time (e.g., 21:00:00)")
    is_open_247: bool = Field(default=False, description="Whether pharmacy is open 24/7")
    ratings: Optional[float] = Field(None, ge=0, le=5, description="Pharmacy rating (0-5)")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    images: Optional[List[str]] = Field(default=None, description="List of pharmacy image URLs")
    logo_url: Optional[str] = Field(None, max_length=255, description="Pharmacy logo URL")


class PharmacyCreate(PharmacyBase):
    """Schema for creating a pharmacy"""
    pass


class PharmacyUpdate(BaseModel):
    """Schema for updating a pharmacy"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    open_time: Optional[time] = None
    close_time: Optional[time] = None
    is_open_247: Optional[bool] = None
    ratings: Optional[float] = Field(None, ge=0, le=5)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PharmacyResponse(PharmacyBase):
    """Response schema for pharmacy"""
    id: int
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_model(cls, pharmacy):
        """Convert ORM model to response, parsing images JSON"""
        import json
        
        images = None
        if pharmacy.image_url:
            try:
                images = json.loads(pharmacy.image_url)
            except:
                images = [pharmacy.image_url] if pharmacy.image_url else None
        
        return cls(
            id=pharmacy.id,
            name=pharmacy.name,
            address=pharmacy.address,
            phone=pharmacy.phone,
            open_time=pharmacy.open_time,
            close_time=pharmacy.close_time,
            is_open_247=pharmacy.is_open_247,
            ratings=pharmacy.ratings,
            latitude=pharmacy.latitude,
            longitude=pharmacy.longitude,
            images=images,
            logo_url=pharmacy.logo_url
        )


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
