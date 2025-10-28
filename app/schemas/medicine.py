from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ===== Medicine Schemas =====

class MedicineBase(BaseModel):
    """Base medicine schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Medicine name")
    description: str = Field(..., min_length=1, description="Medicine description")
    generic_name: Optional[str] = Field(None, max_length=255, description="Generic/scientific name")
    type: Optional[str] = Field(None, max_length=100, description="Medicine type (e.g., tablet, syrup)")
    dosage: Optional[str] = Field(None, max_length=100, description="Dosage information")
    side_effects: Optional[str] = Field(None, description="Side effects")
    suitable_for: Optional[str] = Field(None, max_length=10, description="Suitable for (e.g., adults, children)")
    price: Optional[float] = Field(None, ge=0, description="Base price")
    image_url: Optional[str] = Field(None, max_length=255, description="Medicine image URL")
    disease_id: int = Field(..., description="Related disease ID")


class MedicineCreate(MedicineBase):
    """Schema for creating a medicine"""
    pass


class MedicineUpdate(BaseModel):
    """Schema for updating a medicine"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    generic_name: Optional[str] = Field(None, max_length=255)
    type: Optional[str] = Field(None, max_length=100)
    dosage: Optional[str] = Field(None, max_length=100)
    side_effects: Optional[str] = None
    suitable_for: Optional[str] = Field(None, max_length=10)
    price: Optional[float] = Field(None, ge=0)
    image_url: Optional[str] = Field(None, max_length=255)
    disease_id: Optional[int] = None


class MedicineResponse(MedicineBase):
    """Response schema for medicine"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class MedicineListResponse(BaseModel):
    """Response schema for list of medicines"""
    medicines: list[MedicineResponse]
    total: int
    skip: int
    limit: int


# ===== Medicine-Pharmacy Link Schemas =====

class MedicinePharmacyLinkBase(BaseModel):
    """Base schema for medicine-pharmacy link"""
    medicine_id: int = Field(..., description="Medicine ID")
    pharmacy_id: int = Field(..., description="Pharmacy ID")
    stock: Optional[str] = Field(None, max_length=50, description="Stock status (e.g., 'in stock', 'low stock')")
    price: Optional[float] = Field(None, ge=0, description="Price at this pharmacy")


class MedicinePharmacyLinkCreate(MedicinePharmacyLinkBase):
    """Schema for creating medicine-pharmacy link"""
    pass


class MedicinePharmacyLinkUpdate(BaseModel):
    """Schema for updating medicine-pharmacy link"""
    stock: Optional[str] = Field(None, max_length=50)
    price: Optional[float] = Field(None, ge=0)


class MedicinePharmacyLinkResponse(MedicinePharmacyLinkBase):
    """Response schema for medicine-pharmacy link"""
    id: int
    last_updated: datetime
    
    class Config:
        from_attributes = True


# ===== Pharmacy Medicine Info (with details) =====

class PharmacyMedicineInfo(BaseModel):
    """Medicine information at a specific pharmacy"""
    link_id: int = Field(..., description="Medicine-Pharmacy link ID")
    medicine_id: int
    medicine_name: str
    generic_name: Optional[str]
    type: Optional[str]
    dosage: Optional[str]
    description: str
    side_effects: Optional[str]
    suitable_for: Optional[str]
    image_url: Optional[str]
    stock: Optional[str]
    price: Optional[float]
    last_updated: datetime
    
    class Config:
        from_attributes = True


class PharmacyMedicineListResponse(BaseModel):
    """Response for list of medicines at a pharmacy"""
    pharmacy_id: int
    pharmacy_name: str
    medicines: list[PharmacyMedicineInfo]
    total: int


# ===== Medicine Availability Info (across pharmacies) =====

class MedicinePharmacyAvailability(BaseModel):
    """Pharmacy availability for a specific medicine"""
    link_id: int = Field(..., description="Medicine-Pharmacy link ID")
    pharmacy_id: int
    pharmacy_name: str
    pharmacy_address: str
    pharmacy_phone: Optional[str]
    pharmacy_ratings: Optional[float]
    stock: Optional[str]
    price: Optional[float]
    last_updated: datetime
    
    class Config:
        from_attributes = True


class MedicineAvailabilityResponse(BaseModel):
    """Response for medicine availability across pharmacies"""
    medicine_id: int
    medicine_name: str
    generic_name: Optional[str]
    pharmacies: list[MedicinePharmacyAvailability]
    total_pharmacies: int
