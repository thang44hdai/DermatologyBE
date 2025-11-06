from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ===== Enums =====

class PartnerTypeEnum(str, Enum):
    """Partner type enumeration"""
    PHARMACY_CHAIN = "pharmacy_chain"
    INDEPENDENT_PHARMACY = "independent_pharmacy"
    DISTRIBUTOR = "distributor"
    CLINIC = "clinic"
    HOSPITAL = "hospital"


class PartnerStatusEnum(str, Enum):
    """Partner status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    ACTIVE = "active"


class DocumentTypeEnum(str, Enum):
    """Document type enumeration"""
    BUSINESS_LICENSE = "business_license"
    PHARMACY_LICENSE = "pharmacy_license"
    TAX_REGISTRATION = "tax_registration"
    PROFESSIONAL_LICENSE = "professional_license"
    INSURANCE = "insurance"
    OTHER = "other"


# ===== Partner Document Schemas =====

class PartnerDocumentBase(BaseModel):
    """Base partner document schema"""
    document_type: DocumentTypeEnum = Field(..., description="Type of document")
    document_number: Optional[str] = Field(None, max_length=100, description="Document number")
    issue_date: Optional[datetime] = Field(None, description="Issue date of document")
    expiry_date: Optional[datetime] = Field(None, description="Expiry date of document")
    notes: Optional[str] = Field(None, description="Additional notes")


class PartnerDocumentCreate(PartnerDocumentBase):
    """Schema for creating a partner document"""
    partner_id: int = Field(..., description="Partner ID")


class PartnerDocumentUpdate(BaseModel):
    """Schema for updating a partner document"""
    document_type: Optional[DocumentTypeEnum] = None
    document_number: Optional[str] = Field(None, max_length=100)
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    notes: Optional[str] = None


class PartnerDocumentVerify(BaseModel):
    """Schema for verifying a document"""
    verified: bool = Field(..., description="Verification status")
    notes: Optional[str] = Field(None, description="Verification notes")


class PartnerDocumentResponse(PartnerDocumentBase):
    """Response schema for partner document"""
    id: int
    partner_id: int
    verified: bool
    verified_at: Optional[datetime]
    verified_by: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== Partner Schemas =====

class PartnerBase(BaseModel):
    """Base partner schema"""
    name: str = Field(..., min_length=1, max_length=255, description="Partner name")
    contact_phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    contact_email: Optional[EmailStr] = Field(None, description="Contact email")
    partner_type: PartnerTypeEnum = Field(..., description="Type of partner")
    address: Optional[str] = Field(None, description="Partner address")
    logo_url: Optional[str] = Field(None, max_length=255, description="Logo image URL")
    notes: Optional[str] = Field(None, description="Additional notes")
    parent_partner_id: Optional[int] = Field(None, description="Parent partner ID for multi-branch chains")


class PartnerCreate(PartnerBase):
    """Schema for creating a partner"""
    pass


class PartnerUpdate(BaseModel):
    """Schema for updating a partner"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[EmailStr] = None
    partner_type: Optional[PartnerTypeEnum] = None
    address: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    parent_partner_id: Optional[int] = None


class PartnerApprove(BaseModel):
    """Schema for approving a partner"""
    notes: Optional[str] = Field(None, description="Approval notes")


class PartnerReject(BaseModel):
    """Schema for rejecting a partner"""
    notes: str = Field(..., min_length=1, description="Rejection reason (required)")


class PartnerStatusUpdate(BaseModel):
    """Schema for updating partner status"""
    status: PartnerStatusEnum = Field(..., description="New status")
    notes: Optional[str] = Field(None, description="Status change notes")


class PartnerPhoneVerify(BaseModel):
    """Schema for phone verification"""
    verification_code: str = Field(..., min_length=4, max_length=6, description="Verification code")


class PartnerResponse(PartnerBase):
    """Response schema for partner"""
    id: int
    phone_verified: bool
    phone_verified_at: Optional[datetime]
    status: PartnerStatusEnum
    approved_at: Optional[datetime]
    approved_by: Optional[int]
    rejected_by: Optional[int]
    rejected_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Nested relationships (optional, can be loaded separately)
    documents_count: Optional[int] = Field(None, description="Number of documents")
    pharmacies_count: Optional[int] = Field(None, description="Number of pharmacies")
    users_count: Optional[int] = Field(None, description="Number of users")
    child_partners_count: Optional[int] = Field(None, description="Number of child partners")
    
    class Config:
        from_attributes = True


class PartnerDetailResponse(PartnerResponse):
    """Detailed response with nested relationships"""
    documents: List[PartnerDocumentResponse] = Field(default=[], description="Partner documents")
    
    @classmethod
    def from_orm_with_counts(cls, partner):
        """Convert ORM model to response with counts"""
        return cls(
            id=partner.id,
            name=partner.name,
            contact_phone=partner.contact_phone,
            contact_email=partner.contact_email,
            partner_type=partner.partner_type,
            address=partner.address,
            logo_url=partner.logo_url,
            phone_verified=partner.phone_verified,
            phone_verified_at=partner.phone_verified_at,
            status=partner.status,
            notes=partner.notes,
            approved_at=partner.approved_at,
            approved_by=partner.approved_by,
            rejected_by=partner.rejected_by,
            rejected_at=partner.rejected_at,
            created_at=partner.created_at,
            updated_at=partner.updated_at,
            parent_partner_id=partner.parent_partner_id,
            documents_count=len(partner.documents) if partner.documents else 0,
            pharmacies_count=len(partner.pharmacies) if partner.pharmacies else 0,
            users_count=len(partner.users) if partner.users else 0,
            child_partners_count=len(partner.child_partners) if hasattr(partner, 'child_partners') else 0,
            documents=[PartnerDocumentResponse.from_orm(doc) for doc in partner.documents] if partner.documents else []
        )


class PartnerListResponse(BaseModel):
    """Response schema for list of partners"""
    partners: List[PartnerResponse]
    total: int
    skip: int
    limit: int


class PartnerDocumentListResponse(BaseModel):
    """Response schema for list of partner documents"""
    documents: List[PartnerDocumentResponse]
    total: int
