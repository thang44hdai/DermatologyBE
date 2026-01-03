from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ===== Nested Brand Info for Medicine =====

class BrandInfo(BaseModel):
    """Nested brand information in medicine response"""
    id: int
    name: str
    description: Optional[str]
    logo_path: Optional[str]
    
    class Config:
        from_attributes = True


# ===== Medicine Schemas =====

class MedicineBase(BaseModel):
    """Base medicine schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Medicine name")
    description: str = Field(..., min_length=1, description="Medicine description")
    generic_name: Optional[str] = Field(None, max_length=255, description="Generic/scientific name")
    type: Optional[str] = Field(None, max_length=100, description="Medicine type (e.g., tablet, syrup)")
    dosage: Optional[str] = Field(None, max_length=500, description="Dosage information")
    side_effects: Optional[str] = Field(None, description="Side effects")
    suitable_for: Optional[str] = Field(None, max_length=255, description="Suitable for (e.g., adults, children)")
    price: Optional[float] = Field(None, ge=0, description="Base price")
    images: Optional[List[str]] = Field(None, description="List of medicine image URLs")
    brand_id: Optional[int] = Field(None, description="Brand ID")
    category_id: Optional[int] = Field(None, description="Category ID")
    disease_ids: List[int] = Field(..., min_items=1, description="List of related disease IDs")


class MedicineCreate(MedicineBase):
    """Schema for creating a medicine"""
    pass


class MedicineUpdate(BaseModel):
    """Schema for updating a medicine"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    generic_name: Optional[str] = Field(None, max_length=255)
    type: Optional[str] = Field(None, max_length=100)
    dosage: Optional[str] = Field(None, max_length=500)
    side_effects: Optional[str] = None
    suitable_for: Optional[str] = Field(None, max_length=255)
    price: Optional[float] = Field(None, ge=0)
    images: Optional[List[str]] = None
    brand_id: Optional[int] = None
    category_id: Optional[int] = None
    disease_ids: Optional[List[int]] = Field(None, min_items=1, description="List of related disease IDs")


class MedicineResponse(BaseModel):
    """Response schema for medicine"""
    id: int
    name: str
    description: str
    generic_name: Optional[str]
    type: Optional[str]
    dosage: Optional[str]
    side_effects: Optional[str]
    suitable_for: Optional[str]
    price: Optional[float]
    images: Optional[List[str]]
    brand: Optional[BrandInfo]
    category_id: Optional[int]
    category: Optional[dict] = None
    disease_ids: List[int]
    created_at: datetime
    
    @classmethod
    def from_orm_model(cls, medicine):
        """Convert ORM model to response schema with JSON parsing"""
        import json
        
        images = None
        if medicine.image_url:
            try:
                images = json.loads(medicine.image_url) if isinstance(medicine.image_url, str) else medicine.image_url
            except:
                # Fallback: treat as single image URL
                images = [medicine.image_url]
        
        # Get disease IDs from the many-to-many relationship
        disease_ids = [link.disease_id for link in medicine.disease_links]
        
        # Get brand info if exists
        brand = None
        if medicine.brand:
            brand = BrandInfo.from_orm(medicine.brand)
        
        # Get category info if exists
        category_data = None
        if medicine.category:
            category_data = {
                "id": medicine.category.id,
                "name": medicine.category.name,
                "image_url": medicine.category.image_url
            }
        
        return cls(
            id=medicine.id,
            name=medicine.name,
            description=medicine.description,
            generic_name=medicine.generic_name,
            type=medicine.type,
            dosage=medicine.dosage,
            side_effects=medicine.side_effects,
            suitable_for=medicine.suitable_for,
            price=medicine.price,
            images=images,
            brand=brand,
            category_id=medicine.category_id,
            category=category_data,
            disease_ids=disease_ids,
            created_at=medicine.created_at
        )
    
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
    images: Optional[List[str]] = Field(default=None, description="List of medicine image URLs")
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
