from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
import json

from app.core.dependencies import get_db, get_current_admin
from app.services.medicine_service import medicine_service
from app.schemas.medicine import (
    MedicineCreate,
    MedicineUpdate,
    MedicineResponse,
    MedicineListResponse,
    MedicinePharmacyLinkCreate,
    MedicinePharmacyLinkUpdate,
    MedicinePharmacyLinkResponse,
    PharmacyMedicineListResponse,
    MedicineAvailabilityResponse
)
from app.models.database import User
from app.utils.file_upload import file_upload_service
from app.config.settings import settings

router = APIRouter()


# ===== Medicine CRUD Endpoints =====

@router.post("/", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
async def create_medicine(
    name: str = Form(..., description="Medicine name"),
    description: str = Form(..., description="Medicine description"),
    disease_ids: str = Form(..., description="Comma-separated disease IDs (e.g., '1,2,3')"),
    generic_name: Optional[str] = Form(None, description="Generic/scientific name"),
    type: Optional[str] = Form(None, description="Medicine type (tablet, syrup, etc.)"),
    dosage: Optional[str] = Form(None, description="Dosage information"),
    side_effects: Optional[str] = Form(None, description="Side effects"),
    suitable_for: Optional[str] = Form(None, description="Suitable for (adults/children)"),
    price: Optional[float] = Form(None, description="Base price"),
    images: List[UploadFile] = File(None, description="Medicine image files (multiple)"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Create a new medicine with optional multiple image uploads
    
    **Requires Admin Role**
    
    Args:
        name: Medicine name (required)
        description: Medicine description (required)
        disease_ids: Comma-separated disease IDs like "1,2,3" (required, at least one)
        generic_name: Generic/scientific name (optional)
        type: Medicine type like tablet, syrup (optional)
        dosage: Dosage information (optional)
        side_effects: Side effects (optional)
        suitable_for: Suitable for adults/children (optional)
        price: Base price (optional)
        images: Medicine image files (optional, multiple) - JPG, PNG, etc.
        
    Returns:
        Created medicine information
    """
    # Parse disease_ids from comma-separated string
    try:
        disease_ids_list = [int(id.strip()) for id in disease_ids.split(',')]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid disease_ids format. Use comma-separated integers like '1,2,3'"
        )
    
    if not disease_ids_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one disease ID is required"
        )
    
    # Save images if provided
    image_urls = []
    if images:
        for image in images:
            image_url = await file_upload_service.save_image(
                file=image,
                upload_dir=settings.MEDICINE_IMAGES_DIR,
                prefix="medicine"
            )
            image_urls.append(image_url)
    
    medicine_data = MedicineCreate(
        name=name,
        description=description,
        disease_ids=disease_ids_list,
        generic_name=generic_name,
        type=type,
        dosage=dosage,
        side_effects=side_effects,
        suitable_for=suitable_for,
        price=price,
        images=image_urls if image_urls else None
    )
    
    medicine = medicine_service.create_medicine(db, medicine_data, image_urls=image_urls)
    return MedicineResponse.from_orm_model(medicine)


@router.get("/", response_model=MedicineListResponse)
async def get_medicines(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records"),
    search: Optional[str] = Query(None, description="Search by name or generic name"),
    disease_id: Optional[int] = Query(None, description="Filter by disease ID"),
    medicine_type: Optional[str] = Query(None, description="Filter by medicine type"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get list of medicines with filters
    
    **Requires Admin Role**
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (max 100)
        search: Optional search term for name or generic name
        disease_id: Optional filter by disease ID
        medicine_type: Optional filter by medicine type
        
    Returns:
        List of medicines with pagination info
    """
    medicines, total = medicine_service.get_medicines(
        db=db,
        skip=skip,
        limit=limit,
        search=search,
        disease_id=disease_id,
        medicine_type=medicine_type
    )
    
    # Convert to response models with JSON parsing
    medicine_responses = [MedicineResponse.from_orm_model(medicine) for medicine in medicines]
    
    return {
        "medicines": medicine_responses,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{medicine_id}", response_model=MedicineResponse)
async def get_medicine(
    medicine_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get medicine by ID
    
    **Requires Admin Role**
    
    Args:
        medicine_id: Medicine ID
        
    Returns:
        Medicine information
    """
    medicine = medicine_service.get_medicine(db, medicine_id)
    return MedicineResponse.from_orm_model(medicine)


@router.put("/{medicine_id}", response_model=MedicineResponse)
async def update_medicine(
    medicine_id: int,
    name: Optional[str] = Form(None, description="Medicine name"),
    description: Optional[str] = Form(None, description="Medicine description"),
    disease_ids: Optional[str] = Form(None, description="Comma-separated disease IDs (e.g., '1,2,3')"),
    generic_name: Optional[str] = Form(None, description="Generic/scientific name"),
    type: Optional[str] = Form(None, description="Medicine type"),
    dosage: Optional[str] = Form(None, description="Dosage information"),
    side_effects: Optional[str] = Form(None, description="Side effects"),
    suitable_for: Optional[str] = Form(None, description="Suitable for"),
    price: Optional[float] = Form(None, description="Base price"),
    images: List[UploadFile] = File(None, description="Medicine image files (multiple) - will replace existing images"),
    keep_existing_images: bool = Form(True, description="Keep existing images and append new ones"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Update medicine information with optional multiple image uploads
    
    **Requires Admin Role**
    
    Args:
        medicine_id: Medicine ID to update
        name: Medicine name (optional)
        description: Medicine description (optional)
        disease_ids: Comma-separated disease IDs like "1,2,3" (optional)
        generic_name: Generic/scientific name (optional)
        type: Medicine type (optional)
        dosage: Dosage information (optional)
        side_effects: Side effects (optional)
        suitable_for: Suitable for (optional)
        price: Base price (optional)
        images: Medicine image files (optional, multiple) - new images to add or replace
        keep_existing_images: If True, append new images to existing ones; if False, replace all images
        
    Returns:
        Updated medicine information
    """
    # Get existing medicine
    existing_medicine = medicine_service.get_medicine(db, medicine_id)
    
    # Parse disease_ids if provided
    disease_ids_list = None
    if disease_ids is not None:
        try:
            disease_ids_list = [int(id.strip()) for id in disease_ids.split(',')]
            if not disease_ids_list:
                raise ValueError("Empty list")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid disease_ids format. Use comma-separated integers like '1,2,3'"
            )
    
    # Handle image updates
    image_urls = None
    if images:
        # Parse existing images
        existing_images = []
        if existing_medicine.image_url:
            try:
                existing_images = json.loads(existing_medicine.image_url)
            except:
                if existing_medicine.image_url:
                    existing_images = [existing_medicine.image_url]
        
        # Save new images
        new_image_urls = []
        for image in images:
            image_url = await file_upload_service.save_image(
                file=image,
                upload_dir=settings.MEDICINE_IMAGES_DIR,
                prefix="medicine"
            )
            new_image_urls.append(image_url)
        
        # Combine or replace images
        if keep_existing_images:
            image_urls = existing_images + new_image_urls
        else:
            # Delete old images if replacing
            for old_image in existing_images:
                await file_upload_service.delete_image(old_image)
            image_urls = new_image_urls
    
    # Build update data
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if disease_ids_list is not None:
        update_data["disease_ids"] = disease_ids_list
    if generic_name is not None:
        update_data["generic_name"] = generic_name
    if type is not None:
        update_data["type"] = type
    if dosage is not None:
        update_data["dosage"] = dosage
    if side_effects is not None:
        update_data["side_effects"] = side_effects
    if suitable_for is not None:
        update_data["suitable_for"] = suitable_for
    if price is not None:
        update_data["price"] = price
    
    if not update_data and image_urls is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    medicine_update = MedicineUpdate(**update_data)
    medicine = medicine_service.update_medicine(db, medicine_id, medicine_update, image_urls=image_urls)
    return MedicineResponse.from_orm_model(medicine)


@router.delete("/{medicine_id}")
async def delete_medicine(
    medicine_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Delete a medicine (and all its images)
    
    **Requires Admin Role**
    
    Note: Cannot delete if medicine is linked to any pharmacies
    
    Args:
        medicine_id: Medicine ID to delete
        
    Returns:
        Success message
    """
    # Get medicine to get image paths
    medicine = medicine_service.get_medicine(db, medicine_id)
    
    # Delete medicine from database
    medicine_service.delete_medicine(db, medicine_id)
    
    # Delete all image files
    if medicine.image_url:
        try:
            image_urls = json.loads(medicine.image_url)
            for image_url in image_urls:
                file_upload_service.delete_image(image_url)
        except:
            # Fallback for single image
            if medicine.image_url:
                file_upload_service.delete_image(medicine.image_url)
    
    return {
        "success": True,
        "message": "Medicine deleted successfully",
        "medicine_id": medicine_id
    }


# ===== Medicine-Pharmacy Link Management =====

@router.post("/pharmacy-link", response_model=MedicinePharmacyLinkResponse, status_code=status.HTTP_201_CREATED)
async def add_medicine_to_pharmacy(
    link: MedicinePharmacyLinkCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Add medicine to a pharmacy (create link)
    
    **Requires Admin Role**
    
    Args:
        medicine_id: Medicine ID (required)
        pharmacy_id: Pharmacy ID (required)
        stock: Stock status like 'in stock', 'low stock' (optional)
        price: Price at this pharmacy (optional)
        
    Returns:
        Created medicine-pharmacy link
    """
    return medicine_service.add_medicine_to_pharmacy(db, link)


@router.put("/pharmacy-link/{link_id}", response_model=MedicinePharmacyLinkResponse)
async def update_medicine_pharmacy_link(
    link_id: int,
    link_update: MedicinePharmacyLinkUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Update medicine-pharmacy link (stock and price)
    
    **Requires Admin Role**
    
    Args:
        link_id: Link ID to update
        
    Body: Fields to update (all optional)
        - stock: Stock status
        - price: Price at this pharmacy
        
    Returns:
        Updated link information
    """
    return medicine_service.update_medicine_pharmacy_link(db, link_id, link_update)


@router.delete("/pharmacy-link/{link_id}")
async def remove_medicine_from_pharmacy(
    link_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Remove medicine from pharmacy (delete link)
    
    **Requires Admin Role**
    
    Args:
        link_id: Link ID to delete
        
    Returns:
        Success message
    """
    medicine_service.remove_medicine_from_pharmacy(db, link_id)
    
    return {
        "success": True,
        "message": "Medicine removed from pharmacy successfully",
        "link_id": link_id
    }


# ===== Query Endpoints =====

@router.get("/pharmacy/{pharmacy_id}/medicines", response_model=PharmacyMedicineListResponse)
async def get_pharmacy_medicines(
    pharmacy_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get all medicines available at a specific pharmacy
    
    **Requires Admin Role**
    
    Args:
        pharmacy_id: Pharmacy ID
        skip: Number of records to skip
        limit: Maximum number of records (max 200)
        
    Returns:
        List of medicines at this pharmacy with stock and price info
    """
    return medicine_service.get_pharmacy_medicines(db, pharmacy_id, skip, limit)


@router.get("/{medicine_id}/availability", response_model=MedicineAvailabilityResponse)
async def get_medicine_availability(
    medicine_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get all pharmacies where a medicine is available
    
    **Requires Admin Role**
    
    Args:
        medicine_id: Medicine ID
        
    Returns:
        List of pharmacies with stock and price info for this medicine
    """
    return medicine_service.get_medicine_availability(db, medicine_id)
