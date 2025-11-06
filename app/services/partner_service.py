from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import HTTPException, status
from datetime import datetime

from app.models.database import Partner, PartnerDocument, User, PartnerStatus
from app.schemas.partner import (
    PartnerCreate,
    PartnerUpdate,
    PartnerStatusUpdate,
    PartnerDocumentCreate,
    PartnerDocumentUpdate,
    PartnerDocumentVerify
)


class PartnerService:
    """Service for partner-related operations"""
    
    @staticmethod
    def create_partner(db: Session, partner: PartnerCreate) -> Partner:
        """
        Create a new partner
        
        Args:
            db: Database session
            partner: Partner creation data
            
        Returns:
            Created partner object
        """
        # Check if parent partner exists (if specified)
        if partner.parent_partner_id:
            parent = db.query(Partner).filter(Partner.id == partner.parent_partner_id).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent partner with ID {partner.parent_partner_id} not found"
                )
        
        # Create new partner
        db_partner = Partner(
            name=partner.name,
            contact_phone=partner.contact_phone,
            contact_email=partner.contact_email,
            partner_type=partner.partner_type,
            address=partner.address,
            logo_url=partner.logo_url,
            notes=partner.notes,
            parent_partner_id=partner.parent_partner_id,
            status=PartnerStatus.PENDING  # Default status
        )
        
        db.add(db_partner)
        db.commit()
        db.refresh(db_partner)
        return db_partner
    
    @staticmethod
    def get_partner(db: Session, partner_id: int) -> Partner:
        """
        Get partner by ID
        
        Args:
            db: Database session
            partner_id: Partner ID
            
        Returns:
            Partner object
            
        Raises:
            HTTPException: If partner not found
        """
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Partner not found"
            )
        return partner
    
    @staticmethod
    def get_partners(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        partner_type: Optional[str] = None,
        status: Optional[str] = None,
        parent_partner_id: Optional[int] = None
    ) -> tuple[List[Partner], int]:
        """
        Get list of partners with optional filters
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Optional search term for partner name or email
            partner_type: Optional filter by partner type
            status: Optional filter by status
            parent_partner_id: Optional filter by parent partner ID
            
        Returns:
            Tuple of (list of partners, total count)
        """
        query = db.query(Partner)
        
        # Apply filters
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Partner.name.ilike(search_filter)) |
                (Partner.contact_email.ilike(search_filter))
            )
        
        if partner_type:
            query = query.filter(Partner.partner_type == partner_type)
        
        if status:
            query = query.filter(Partner.status == status)
        
        if parent_partner_id is not None:
            query = query.filter(Partner.parent_partner_id == parent_partner_id)
        
        total = query.count()
        partners = query.offset(skip).limit(limit).all()
        
        return partners, total
    
    @staticmethod
    def update_partner(
        db: Session,
        partner_id: int,
        partner_update: PartnerUpdate
    ) -> Partner:
        """
        Update partner information
        
        Args:
            db: Database session
            partner_id: Partner ID
            partner_update: Partner update data
            
        Returns:
            Updated partner object
        """
        db_partner = PartnerService.get_partner(db, partner_id)
        
        # Check if parent partner exists (if being updated)
        if partner_update.parent_partner_id is not None:
            if partner_update.parent_partner_id == partner_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Partner cannot be its own parent"
                )
            
            parent = db.query(Partner).filter(Partner.id == partner_update.parent_partner_id).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Parent partner with ID {partner_update.parent_partner_id} not found"
                )
        
        # Update fields if provided
        update_data = partner_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_partner, field, value)
        
        db.commit()
        db.refresh(db_partner)
        return db_partner
    
    @staticmethod
    def update_partner_status(
        db: Session,
        partner_id: int,
        status_update: PartnerStatusUpdate,
        admin_id: int
    ) -> Partner:
        """
        Update partner status (admin only)
        
        Args:
            db: Database session
            partner_id: Partner ID
            status_update: Status update data
            admin_id: Admin user ID performing the action
            
        Returns:
            Updated partner object
        """
        db_partner = PartnerService.get_partner(db, partner_id)
        
        db_partner.status = status_update.status
        if status_update.notes:
            db_partner.notes = status_update.notes
        
        db.commit()
        db.refresh(db_partner)
        return db_partner
    
    @staticmethod
    def approve_partner(
        db: Session,
        partner_id: int,
        admin_id: int,
        notes: Optional[str] = None
    ) -> Partner:
        """
        Approve a partner (admin only)
        
        Args:
            db: Database session
            partner_id: Partner ID
            admin_id: Admin user ID performing the approval
            notes: Optional approval notes
            
        Returns:
            Approved partner object
        """
        db_partner = PartnerService.get_partner(db, partner_id)
        
        if db_partner.status == PartnerStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Partner is already approved"
            )
        
        db_partner.status = PartnerStatus.APPROVED
        db_partner.approved_at = datetime.now()
        db_partner.approved_by = admin_id
        if notes:
            db_partner.notes = notes
        
        db.commit()
        db.refresh(db_partner)
        return db_partner
    
    @staticmethod
    def reject_partner(
        db: Session,
        partner_id: int,
        admin_id: int,
        notes: str
    ) -> Partner:
        """
        Reject a partner (admin only)
        
        Args:
            db: Database session
            partner_id: Partner ID
            admin_id: Admin user ID performing the rejection
            notes: Rejection reason (required)
            
        Returns:
            Rejected partner object
        """
        db_partner = PartnerService.get_partner(db, partner_id)
        
        if db_partner.status == PartnerStatus.REJECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Partner is already rejected"
            )
        
        db_partner.status = PartnerStatus.REJECTED
        db_partner.rejected_at = datetime.now()
        db_partner.rejected_by = admin_id
        db_partner.notes = notes
        
        db.commit()
        db.refresh(db_partner)
        return db_partner
    
    @staticmethod
    def delete_partner(db: Session, partner_id: int) -> None:
        """
        Delete a partner
        
        Args:
            db: Database session
            partner_id: Partner ID
            
        Note:
            This will cascade delete all partner documents.
            Pharmacies and users will have their partner_id set to NULL.
        """
        db_partner = PartnerService.get_partner(db, partner_id)
        db.delete(db_partner)
        db.commit()
    
    @staticmethod
    def verify_phone(
        db: Session,
        partner_id: int,
        verification_code: str
    ) -> Partner:
        """
        Verify partner phone number
        
        Args:
            db: Database session
            partner_id: Partner ID
            verification_code: Verification code
            
        Returns:
            Updated partner object
            
        Note:
            This is a simplified version. In production, you would:
            1. Send SMS with verification code
            2. Store code in cache/database
            3. Validate against stored code
        """
        db_partner = PartnerService.get_partner(db, partner_id)
        
        if db_partner.phone_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already verified"
            )
        
        # TODO: Implement actual verification logic
        # For now, accept any 4-6 digit code
        if not verification_code.isdigit() or len(verification_code) < 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
        
        db_partner.phone_verified = True
        db_partner.phone_verified_at = datetime.now()
        
        db.commit()
        db.refresh(db_partner)
        return db_partner


class PartnerDocumentService:
    """Service for partner document operations"""
    
    @staticmethod
    def create_document(db: Session, document: PartnerDocumentCreate) -> PartnerDocument:
        """
        Create a new partner document
        
        Args:
            db: Database session
            document: Document creation data
            
        Returns:
            Created document object
        """
        # Check if partner exists
        partner = db.query(Partner).filter(Partner.id == document.partner_id).first()
        if not partner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Partner with ID {document.partner_id} not found"
            )
        
        # Create document
        db_document = PartnerDocument(
            partner_id=document.partner_id,
            document_type=document.document_type,
            document_number=document.document_number,
            issue_date=document.issue_date,
            expiry_date=document.expiry_date,
            notes=document.notes
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        return db_document
    
    @staticmethod
    def get_document(db: Session, document_id: int) -> PartnerDocument:
        """Get document by ID"""
        document = db.query(PartnerDocument).filter(PartnerDocument.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        return document
    
    @staticmethod
    def get_partner_documents(
        db: Session,
        partner_id: int,
        document_type: Optional[str] = None,
        verified: Optional[bool] = None
    ) -> List[PartnerDocument]:
        """
        Get all documents for a partner
        
        Args:
            db: Database session
            partner_id: Partner ID
            document_type: Optional filter by document type
            verified: Optional filter by verification status
            
        Returns:
            List of documents
        """
        query = db.query(PartnerDocument).filter(PartnerDocument.partner_id == partner_id)
        
        if document_type:
            query = query.filter(PartnerDocument.document_type == document_type)
        
        if verified is not None:
            query = query.filter(PartnerDocument.verified == verified)
        
        return query.all()
    
    @staticmethod
    def update_document(
        db: Session,
        document_id: int,
        document_update: PartnerDocumentUpdate
    ) -> PartnerDocument:
        """Update document information"""
        db_document = PartnerDocumentService.get_document(db, document_id)
        
        update_data = document_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_document, field, value)
        
        db.commit()
        db.refresh(db_document)
        return db_document
    
    @staticmethod
    def verify_document(
        db: Session,
        document_id: int,
        verify_data: PartnerDocumentVerify,
        admin_id: int
    ) -> PartnerDocument:
        """
        Verify a partner document (admin only)
        
        Args:
            db: Database session
            document_id: Document ID
            verify_data: Verification data
            admin_id: Admin user ID performing the verification
            
        Returns:
            Verified document object
        """
        db_document = PartnerDocumentService.get_document(db, document_id)
        
        db_document.verified = verify_data.verified
        db_document.verified_at = datetime.now()
        db_document.verified_by = admin_id
        if verify_data.notes:
            db_document.notes = verify_data.notes
        
        db.commit()
        db.refresh(db_document)
        return db_document
    
    @staticmethod
    def delete_document(db: Session, document_id: int) -> None:
        """Delete a document"""
        db_document = PartnerDocumentService.get_document(db, document_id)
        db.delete(db_document)
        db.commit()
