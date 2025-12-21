from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import HTTPException, status

from app.models import Brand
from app.schemas.brand import BrandCreate, BrandUpdate


class BrandService:
    """Service for brand-related operations"""
    
    @staticmethod
    def create_brand(db: Session, brand: BrandCreate) -> Brand:
        """
        Create a new brand
        
        Args:
            db: Database session
            brand: Brand creation data
            
        Returns:
            Created brand object
            
        Raises:
            HTTPException: If brand with same name already exists
        """
        # Check if brand with same name already exists
        existing = db.query(Brand).filter(Brand.name == brand.name).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Brand with name '{brand.name}' already exists"
            )
        
        # Create new brand
        db_brand = Brand(
            name=brand.name,
            description=brand.description,
            logo_path=brand.logo_path
        )
        
        db.add(db_brand)
        db.commit()
        db.refresh(db_brand)
        return db_brand
    
    @staticmethod
    def get_brand(db: Session, brand_id: int) -> Brand:
        """
        Get brand by ID
        
        Args:
            db: Database session
            brand_id: Brand ID
            
        Returns:
            Brand object
            
        Raises:
            HTTPException: If brand not found
        """
        brand = db.query(Brand).filter(Brand.id == brand_id).first()
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand not found"
            )
        return brand
    
    @staticmethod
    def get_brand_by_name(db: Session, name: str) -> Optional[Brand]:
        """
        Get brand by name
        
        Args:
            db: Database session
            name: Brand name
            
        Returns:
            Brand object or None
        """
        return db.query(Brand).filter(Brand.name == name).first()
    
    @staticmethod
    def get_brands(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> tuple[List[Brand], int]:
        """
        Get list of brands with optional search
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Optional search term for brand name
            
        Returns:
            Tuple of (list of brands, total count)
        """
        query = db.query(Brand)
        
        # Apply search filter if provided
        if search:
            search_filter = f"%{search}%"
            query = query.filter(Brand.name.ilike(search_filter))
        
        total = query.count()
        brands = query.offset(skip).limit(limit).all()
        
        return brands, total
    
    @staticmethod
    def update_brand(
        db: Session,
        brand_id: int,
        brand_update: BrandUpdate
    ) -> Brand:
        """
        Update brand information
        
        Args:
            db: Database session
            brand_id: Brand ID
            brand_update: Brand update data
            
        Returns:
            Updated brand object
            
        Raises:
            HTTPException: If brand not found or name already exists
        """
        # Get existing brand
        db_brand = BrandService.get_brand(db, brand_id)
        
        # Check if name is being updated and if it already exists
        if brand_update.name and brand_update.name != db_brand.name:
            existing = db.query(Brand).filter(Brand.name == brand_update.name).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Brand with name '{brand_update.name}' already exists"
                )
        
        # Update fields if provided
        update_data = brand_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_brand, field, value)
        
        db.commit()
        db.refresh(db_brand)
        return db_brand
    
    @staticmethod
    def delete_brand(db: Session, brand_id: int) -> None:
        """
        Delete a brand
        
        Args:
            db: Database session
            brand_id: Brand ID
            
        Raises:
            HTTPException: If brand not found
            
        Note:
            Due to ON DELETE SET NULL constraint, associated medicines 
            will have their brand_id set to NULL when brand is deleted
        """
        db_brand = BrandService.get_brand(db, brand_id)
        db.delete(db_brand)
        db.commit()
    
    @staticmethod
    def update_brand_logo(db: Session, brand_id: int, logo_path: str) -> Brand:
        """
        Update brand logo path
        
        Args:
            db: Database session
            brand_id: Brand ID
            logo_path: New logo file path
            
        Returns:
            Updated brand object
        """
        db_brand = BrandService.get_brand(db, brand_id)
        db_brand.logo_path = logo_path
        
        db.commit()
        db.refresh(db_brand)
        return db_brand
