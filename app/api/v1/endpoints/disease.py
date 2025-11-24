from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional

from app.core.dependencies import get_db, get_current_admin
from app.services.disease_service import disease_service
from app.schemas.disease import (
    DiseaseCreate,
    DiseaseUpdate,
    DiseaseResponse,
    DiseaseListResponse,
    DiseaseDetailResponse
)
from app.models.database import User
from app.utils.file_upload import file_upload_service
from app.config.settings import settings

router = APIRouter()


@router.post("/", response_model=DiseaseResponse, status_code=status.HTTP_201_CREATED)
async def create_disease(
    disease_name: str = Form(..., description="Disease name"),
    description: Optional[str] = Form(None, description="Disease description"),
    symptoms: Optional[str] = Form(None, description="Disease symptoms"),
    treatment: Optional[str] = Form(None, description="Treatment information"),
    image: Optional[UploadFile] = File(None, description="Disease image file"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Create a new disease with optional image upload
    
    **Requires Admin Role**
    
    Args:
        disease_name: Disease name (required)
        description: Disease description (optional)
        symptoms: Disease symptoms (optional)
        treatment: Treatment information (optional)
        image: Disease image file (optional) - JPG, PNG, etc.
        
    Returns:
        Created disease information
    """
    # Save image if provided
    image_url = None
    if image:
        image_url = await file_upload_service.save_image(
            file=image,
            upload_dir=settings.DISEASE_IMAGES_DIR,
            prefix="disease"
        )
    
    disease_data = DiseaseCreate(
        disease_name=disease_name,
        description=description,
        symptoms=symptoms,
        treatment=treatment,
        image_url=image_url
    )
    
    return disease_service.create_disease(db, disease_data)


@router.get("/", response_model=DiseaseListResponse)
async def get_diseases(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records"),
    search: Optional[str] = Query(None, description="Search by disease name"),
    db: Session = Depends(get_db)
):
    """
    Get list of diseases with search and medicines
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (max 100)
        search: Optional search term for disease name
        
    Returns:
        List of diseases with medicines and pagination info
    """
    diseases, total = disease_service.get_diseases_with_medicines(
        db=db,
        skip=skip,
        limit=limit,
        search=search
    )
    
    return {
        "diseases": diseases,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{disease_id}", response_model=DiseaseDetailResponse)
async def get_disease(
    disease_id: int,
    db: Session = Depends(get_db)
):
    """
    Get disease by ID with medicines list
    
    Args:
        disease_id: Disease ID
        
    Returns:
        Disease information with related medicines
    """
    return disease_service.get_disease_detail(db, disease_id)


# @router.get("/{disease_id}/detail", response_model=DiseaseDetailResponse)
# async def get_disease_detail(
#     disease_id: int,
#     db: Session = Depends(get_db)
# ):
#     """
#     Get disease with detailed statistics
    
#     Returns disease information with counts of:
#     - Related medicines
#     - Diagnosis history records
    
#     Args:
#         disease_id: Disease ID
        
#     Returns:
#         Disease information with related counts
#     """
#     return disease_service.get_disease_detail(db, disease_id)


@router.put("/{disease_id}", response_model=DiseaseResponse)
async def update_disease(
    disease_id: int,
    disease_name: Optional[str] = Form(None, description="Disease name"),
    description: Optional[str] = Form(None, description="Disease description"),
    symptoms: Optional[str] = Form(None, description="Disease symptoms"),
    treatment: Optional[str] = Form(None, description="Treatment information"),
    image: Optional[UploadFile] = File(None, description="Disease image file"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Update disease information with optional image upload
    
    **Requires Admin Role**
    
    Args:
        disease_id: Disease ID to update
        disease_name: Disease name (optional)
        description: Disease description (optional)
        symptoms: Disease symptoms (optional)
        treatment: Treatment information (optional)
        image: Disease image file (optional) - will replace existing image
        
    Returns:
        Updated disease information
    """
    # Get existing disease to get old image path
    existing_disease = disease_service.get_disease(db, disease_id)
    
    # Handle image update
    image_url = None
    if image:
        image_url = await file_upload_service.update_image(
            file=image,
            old_file_path=existing_disease.image_url,
            upload_dir=settings.DISEASE_IMAGES_DIR,
            prefix="disease"
        )
    
    # Build update data
    update_data = {}
    if disease_name is not None:
        update_data["disease_name"] = disease_name
    if description is not None:
        update_data["description"] = description
    if symptoms is not None:
        update_data["symptoms"] = symptoms
    if treatment is not None:
        update_data["treatment"] = treatment
    if image_url is not None:
        update_data["image_url"] = image_url
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    disease_update = DiseaseUpdate(**update_data)
    return disease_service.update_disease(db, disease_id, disease_update)


@router.delete("/{disease_id}")
async def delete_disease(
    disease_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Delete a disease (and its image)
    
    **Requires Admin Role**
    
    Note: Cannot delete if disease has related medicines or diagnosis records
    
    Args:
        disease_id: Disease ID to delete
        
    Returns:
        Success message
    """
    # Get disease to get image path
    disease = disease_service.get_disease(db, disease_id)
    
    # Delete disease from database
    disease_service.delete_disease(db, disease_id)
    
    # Delete image file
    if disease.image_url:
        file_upload_service.delete_image(disease.image_url)
    
    return {
        "success": True,
        "message": "Disease deleted successfully",
        "disease_id": disease_id
    }
