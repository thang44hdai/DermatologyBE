from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from app.core.dependencies import get_db, get_current_admin
from app.services.brand_service import BrandService
from app.schemas.brand import (
    BrandCreate,
    BrandUpdate,
    BrandResponse,
    BrandListResponse,
    BrandMedicinesResponse
)
from app.models import User
from app.utils.file_upload import FileUploadService

router = APIRouter()


@router.post("/", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    brand: BrandCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Create a new brand
    
    **Requires Admin Role**
    
    Args:
        brand: Brand creation data (name, description, logo_path)
        
    Returns:
        Created brand information
    """
    db_brand = BrandService.create_brand(db, brand)
    return BrandResponse.from_orm(db_brand)


@router.get("/", response_model=BrandListResponse)
async def get_brands(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records"),
    search: Optional[str] = Query(None, description="Search by brand name"),
    db: Session = Depends(get_db)
):
    """
    Get list of brands with pagination and optional search
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        search: Optional search term for brand name
        
    Returns:
        List of brands with pagination info
    """
    brands, total = BrandService.get_brands(db, skip, limit, search)
    
    brand_responses = [BrandResponse.from_orm(brand) for brand in brands]
    
    return BrandListResponse(
        brands=brand_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: int,
    db: Session = Depends(get_db)
):
    """
    Get brand by ID
    
    Args:
        brand_id: Brand ID
        
    Returns:
        Brand information
    """
    brand = BrandService.get_brand(db, brand_id)
    return BrandResponse.from_orm(brand)


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: int,
    brand_update: BrandUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Update brand information
    
    **Requires Admin Role**
    
    Args:
        brand_id: Brand ID
        brand_update: Brand update data (all fields optional)
        
    Returns:
        Updated brand information
    """
    brand = BrandService.update_brand(db, brand_id, brand_update)
    return BrandResponse.from_orm(brand)


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Delete a brand
    
    **Requires Admin Role**
    
    Args:
        brand_id: Brand ID
        
    Note:
        Medicines associated with this brand will have their brand_id set to NULL
    """
    BrandService.delete_brand(db, brand_id)
    return None


@router.post("/{brand_id}/logo", response_model=BrandResponse)
async def upload_brand_logo(
    brand_id: int,
    logo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Upload logo image for a brand
    
    **Requires Admin Role**
    
    Args:
        brand_id: Brand ID
        logo: Logo image file
        
    Returns:
        Updated brand information with new logo path
    """
    # Validate file is an image
    FileUploadService.validate_image_file(logo)
    
    # Save logo image
    try:
        logo_path = await FileUploadService.save_image(logo, "uploads/brands")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save logo: {str(e)}"
        )
    
    # Update brand with new logo path
    brand = BrandService.update_brand_logo(db, brand_id, logo_path)
    return BrandResponse.from_orm(brand)


@router.get("/name/{brand_name}", response_model=BrandResponse)
async def get_brand_by_name(
    brand_name: str,
    db: Session = Depends(get_db)
):
    """
    Get brand by name
    
    Args:
        brand_name: Brand name (exact match, case-insensitive)
        
    Returns:
        Brand information
    """
    brand = BrandService.get_brand_by_name(db, brand_name)
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with name '{brand_name}' not found"
        )
    return BrandResponse.from_orm(brand)


@router.get("/{brand_id}/medicines", response_model=BrandMedicinesResponse)
def get_medicines_by_brand(
    brand_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all medicines for a specific brand
    
    Args:
        brand_id: Brand ID
        skip: Offset for pagination
        limit: Number of items (max 100)
        
    Returns:
        Brand info and list of medicines with example response
    """
    from app.models import Medicines
    import json
    
    # Get brand
    brand = BrandService.get_brand(db, brand_id)
    
    # Get medicines for this brand
    medicines_query = db.query(Medicines).filter(Medicines.brand_id == brand_id)
    total = medicines_query.count()
    medicines = medicines_query.offset(skip).limit(limit).all()
    
    # Parse medicine images from JSON
    medicines_data = []
    for medicine in medicines:
        # Parse images
        images = []
        if medicine.image_url:
            try:
                images = json.loads(medicine.image_url)
            except:
                images = [medicine.image_url] if medicine.image_url else []
        
        medicines_data.append({
            "id": medicine.id,
            "name": medicine.name,
            "description": medicine.description,
            "generic_name": medicine.generic_name,
            "type": medicine.type,
            "dosage": medicine.dosage,
            "price": medicine.price,
            "images": images
        })
    
    return {
        "brand": {
            "id": brand.id,
            "name": brand.name,
            "logo_path": brand.logo_path
        },
        "medicines": medicines_data,
        "total": total,
        "skip": skip,
        "limit": limit
    }

