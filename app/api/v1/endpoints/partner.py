from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List

from app.core.dependencies import get_db, get_current_admin, get_current_user
from app.services.partner_service import PartnerService, PartnerDocumentService
from app.schemas.partner import (
    PartnerCreate,
    PartnerUpdate,
    PartnerResponse,
    PartnerDetailResponse,
    PartnerListResponse,
    PartnerApprove,
    PartnerReject,
    PartnerStatusUpdate,
    PartnerPhoneVerify,
    PartnerDocumentCreate,
    PartnerDocumentUpdate,
    PartnerDocumentResponse,
    PartnerDocumentListResponse,
    PartnerDocumentVerify,
    PartnerTypeEnum,
    PartnerStatusEnum,
    DocumentTypeEnum
)
from app.models.database import User
from app.utils.file_upload import FileUploadService

router = APIRouter()


# ===== Partner Endpoints =====

@router.post("/", response_model=PartnerResponse, status_code=status.HTTP_201_CREATED)
async def create_partner(
    partner: PartnerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new partner
    
    Any authenticated user can register as a partner.
    Partner will be in PENDING status by default and requires admin approval.
    
    Args:
        partner: Partner creation data
        
    Returns:
        Created partner information
    """
    db_partner = PartnerService.create_partner(db, partner)
    return PartnerResponse.from_orm(db_partner)


@router.get("/", response_model=PartnerListResponse)
async def get_partners(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    partner_type: Optional[PartnerTypeEnum] = Query(None, description="Filter by partner type"),
    status: Optional[PartnerStatusEnum] = Query(None, description="Filter by status"),
    parent_partner_id: Optional[int] = Query(None, description="Filter by parent partner ID"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get list of partners with pagination and filters
    
    **Requires Admin Role**
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        search: Optional search term for name or email
        partner_type: Optional filter by partner type
        status: Optional filter by status
        parent_partner_id: Optional filter by parent partner
        
    Returns:
        List of partners with pagination info
    """
    partners, total = PartnerService.get_partners(
        db, skip, limit, search,
        partner_type.value if partner_type else None,
        status.value if status else None,
        parent_partner_id
    )
    
    partner_responses = [PartnerResponse.from_orm(p) for p in partners]
    
    return PartnerListResponse(
        partners=partner_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{partner_id}", response_model=PartnerDetailResponse)
async def get_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get partner by ID with detailed information
    
    **Requires Admin Role**
    
    Args:
        partner_id: Partner ID
        
    Returns:
        Partner detailed information with documents
    """
    partner = PartnerService.get_partner(db, partner_id)
    return PartnerDetailResponse.from_orm_with_counts(partner)


@router.put("/{partner_id}", response_model=PartnerResponse)
async def update_partner(
    partner_id: int,
    partner_update: PartnerUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Update partner information
    
    **Requires Admin Role**
    
    Args:
        partner_id: Partner ID
        partner_update: Partner update data (all fields optional)
        
    Returns:
        Updated partner information
    """
    partner = PartnerService.update_partner(db, partner_id, partner_update)
    return PartnerResponse.from_orm(partner)


@router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_partner(
    partner_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Delete a partner
    
    **Requires Admin Role**
    
    Args:
        partner_id: Partner ID
        
    Note:
        - Partner documents will be cascade deleted
        - Pharmacies and users will have their partner_id set to NULL
    """
    PartnerService.delete_partner(db, partner_id)
    return None


@router.post("/{partner_id}/logo", response_model=PartnerResponse)
async def upload_partner_logo(
    partner_id: int,
    logo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Upload logo image for a partner
    
    **Requires Admin Role**
    
    Args:
        partner_id: Partner ID
        logo: Logo image file
        
    Returns:
        Updated partner information with new logo URL
    """
    # Validate file is an image
    FileUploadService.validate_image_file(logo)
    
    # Save logo image
    try:
        logo_url = await FileUploadService.save_image(logo, "uploads/partners")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save logo: {str(e)}"
        )
    
    # Update partner with new logo URL
    partner_update = PartnerUpdate(logo_url=logo_url)
    partner = PartnerService.update_partner(db, partner_id, partner_update)
    return PartnerResponse.from_orm(partner)


# ===== Partner Status Management =====

@router.post("/{partner_id}/approve", response_model=PartnerResponse)
async def approve_partner(
    partner_id: int,
    approve_data: PartnerApprove,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Approve a partner application
    
    **Requires Admin Role**
    
    Args:
        partner_id: Partner ID
        approve_data: Optional approval notes
        
    Returns:
        Approved partner information
    """
    partner = PartnerService.approve_partner(
        db, partner_id, current_admin.id, approve_data.notes
    )
    return PartnerResponse.from_orm(partner)


@router.post("/{partner_id}/reject", response_model=PartnerResponse)
async def reject_partner(
    partner_id: int,
    reject_data: PartnerReject,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Reject a partner application
    
    **Requires Admin Role**
    
    Args:
        partner_id: Partner ID
        reject_data: Rejection reason (required)
        
    Returns:
        Rejected partner information
    """
    partner = PartnerService.reject_partner(
        db, partner_id, current_admin.id, reject_data.notes
    )
    return PartnerResponse.from_orm(partner)


@router.put("/{partner_id}/status", response_model=PartnerResponse)
async def update_partner_status(
    partner_id: int,
    status_update: PartnerStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Update partner status
    
    **Requires Admin Role**
    
    Args:
        partner_id: Partner ID
        status_update: New status and optional notes
        
    Returns:
        Updated partner information
    """
    partner = PartnerService.update_partner_status(
        db, partner_id, status_update, current_admin.id
    )
    return PartnerResponse.from_orm(partner)


@router.post("/{partner_id}/verify-phone", response_model=PartnerResponse)
async def verify_partner_phone(
    partner_id: int,
    verify_data: PartnerPhoneVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify partner phone number
    
    Args:
        partner_id: Partner ID
        verify_data: Verification code
        
    Returns:
        Updated partner information
        
    Note:
        This is a simplified implementation.
        In production, implement proper SMS verification.
    """
    partner = PartnerService.verify_phone(db, partner_id, verify_data.verification_code)
    return PartnerResponse.from_orm(partner)


# ===== Partner Child Branches =====

@router.get("/{partner_id}/children", response_model=PartnerListResponse)
async def get_child_partners(
    partner_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get child partners (branches) of a parent partner
    
    **Requires Admin Role**
    
    Args:
        partner_id: Parent partner ID
        skip: Number of records to skip
        limit: Maximum number of records
        
    Returns:
        List of child partners
    """
    partners, total = PartnerService.get_partners(
        db, skip, limit,
        parent_partner_id=partner_id
    )
    
    partner_responses = [PartnerResponse.from_orm(p) for p in partners]
    
    return PartnerListResponse(
        partners=partner_responses,
        total=total,
        skip=skip,
        limit=limit
    )


# ===== Partner Document Endpoints =====

@router.post("/{partner_id}/documents", response_model=PartnerDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_partner_document(
    partner_id: int,
    document: PartnerDocumentCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Create a new document for a partner
    
    **Requires Admin Role**
    
    Args:
        partner_id: Partner ID
        document: Document creation data
        
    Returns:
        Created document information
    """
    # Ensure partner_id in path matches document data
    if document.partner_id != partner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Partner ID in path must match document data"
        )
    
    db_document = PartnerDocumentService.create_document(db, document)
    return PartnerDocumentResponse.from_orm(db_document)


@router.get("/{partner_id}/documents", response_model=PartnerDocumentListResponse)
async def get_partner_documents(
    partner_id: int,
    document_type: Optional[DocumentTypeEnum] = Query(None, description="Filter by document type"),
    verified: Optional[bool] = Query(None, description="Filter by verification status"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get all documents for a partner
    
    **Requires Admin Role**
    
    Args:
        partner_id: Partner ID
        document_type: Optional filter by document type
        verified: Optional filter by verification status
        
    Returns:
        List of partner documents
    """
    documents = PartnerDocumentService.get_partner_documents(
        db, partner_id,
        document_type.value if document_type else None,
        verified
    )
    
    document_responses = [PartnerDocumentResponse.from_orm(doc) for doc in documents]
    
    return PartnerDocumentListResponse(
        documents=document_responses,
        total=len(document_responses)
    )


@router.get("/documents/{document_id}", response_model=PartnerDocumentResponse)
async def get_partner_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get document by ID
    
    **Requires Admin Role**
    
    Args:
        document_id: Document ID
        
    Returns:
        Document information
    """
    document = PartnerDocumentService.get_document(db, document_id)
    return PartnerDocumentResponse.from_orm(document)


@router.put("/documents/{document_id}", response_model=PartnerDocumentResponse)
async def update_partner_document(
    document_id: int,
    document_update: PartnerDocumentUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Update document information
    
    **Requires Admin Role**
    
    Args:
        document_id: Document ID
        document_update: Document update data (all fields optional)
        
    Returns:
        Updated document information
    """
    document = PartnerDocumentService.update_document(db, document_id, document_update)
    return PartnerDocumentResponse.from_orm(document)


@router.post("/documents/{document_id}/verify", response_model=PartnerDocumentResponse)
async def verify_partner_document(
    document_id: int,
    verify_data: PartnerDocumentVerify,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Verify a partner document
    
    **Requires Admin Role**
    
    Args:
        document_id: Document ID
        verify_data: Verification status and optional notes
        
    Returns:
        Verified document information
    """
    document = PartnerDocumentService.verify_document(
        db, document_id, verify_data, current_admin.id
    )
    return PartnerDocumentResponse.from_orm(document)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_partner_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Delete a partner document
    
    **Requires Admin Role**
    
    Args:
        document_id: Document ID
    """
    PartnerDocumentService.delete_document(db, document_id)
    return None
