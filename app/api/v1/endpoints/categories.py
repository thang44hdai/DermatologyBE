from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.dependencies import get_db
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services.category_service import category_service
from app.models.database import User
from app.core.dependencies import get_current_user, get_current_admin
from fastapi import Form

router = APIRouter()


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    name: str = Form(..., description="Category name"),
    image: Optional[UploadFile] = File(None, description="Category image file"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new category with optional image upload (Admin only)
    
    Args:
        name: Category name (required)
        image: Category image file (optional) - JPG, PNG, max 5MB
        
    Returns:
        Created category
    """
    # Validate and upload image if provided
    image_url = None
    if image:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Validate file size (max 5MB)
        contents = await image.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 5MB"
            )
        await image.seek(0)  # Reset file pointer
    
    # Create category
    category_data = CategoryCreate(name=name)
    category = category_service.create_category(db, category_data)
    
    # Upload image after category creation (to use category ID in path)
    if image:
        from app.utils.firebase_storage import upload_image_to_firebase
        folder = f"categories/{category.id}"
        image_url = await upload_image_to_firebase(image, folder)
        
        # Update category with image URL
        category.image_url = image_url
        db.commit()
        db.refresh(category)
    
    # Add medicine count
    category.medicine_count = 0
    
    return category


@router.get("/", response_model=List[CategoryResponse])
def get_all_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    include_count: bool = Query(True),
    db: Session = Depends(get_db)
):
    """
    Get all categories
    
    Query Parameters:
        skip: Offset for pagination
        limit: Number of items (max 100)
        is_active: Filter by active status
        include_count: Include medicine count per category
        
    Returns:
        List of categories
    """
    categories = category_service.get_all_categories(
        db, skip, limit, is_active, include_count
    )
    return categories


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single category by ID
    
    Args:
        category_id: Category ID
        
    Returns:
        Category details
    """
    category = category_service.get_category(db, category_id)
    
    # Add medicine count
    from app.models.database import Medicines
    category.medicine_count = db.query(Medicines).filter(
        Medicines.category_id == category_id
    ).count()
    
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    name: Optional[str] = Form(None, description="Category name"),
    image: Optional[UploadFile] = File(None, description="Category image file"),
    is_active: Optional[bool] = Form(None, description="Active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update a category with optional image upload (Admin only)
    
    Args:
        category_id: Category ID
        name: Category name (optional)
        image: Category image file (optional) - JPG, PNG, max 5MB
        is_active: Active status (optional)
        
    Returns:
        Updated category
    """
    # Validate and upload image if provided
    if image:
        # Validate file type
        if not image.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Validate file size (max 5MB)
        contents = await image.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 5MB"
            )
        await image.seek(0)  # Reset file pointer
        
        # Upload to Firebase
        from app.utils.firebase_storage import upload_image_to_firebase
        folder = f"categories/{category_id}"
        image_url = await upload_image_to_firebase(image, folder)
        
        # Get category and update image
        category = category_service.get_category(db, category_id)
        category.image_url = image_url
    
    # Build update data
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if is_active is not None:
        update_data["is_active"] = is_active
    
    # Update category if there's data to update
    if update_data:
        category_update = CategoryUpdate(**update_data)
        category = category_service.update_category(db, category_id, category_update)
    elif image:
        # Just commit the image update
        db.commit()
        db.refresh(category)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Add medicine count
    from app.models.database import Medicines
    category.medicine_count = db.query(Medicines).filter(
        Medicines.category_id == category_id
    ).count()
    
    return category


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Soft delete a category (Admin only)
    
    Sets is_active=false and removes category from all medicines
    
    Args:
        category_id: Category ID
        
    Returns:
        Success message
    """
    return category_service.delete_category(db, category_id)



@router.get("/{category_id}/medicines")
def get_medicines_by_category(
    category_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all medicines in a category
    
    Args:
        category_id: Category ID
        skip: Offset for pagination
        limit: Number of items (max 100)
        
    Returns:
        Category info and list of medicines
    """
    result = category_service.get_medicines_by_category(db, category_id, skip, limit)
    
    return {
        "category": {
            "id": result["category"].id,
            "name": result["category"].name,
            "image_url": result["category"].image_url
        },
        "medicines": result["medicines"],
        "total": result["total"],
        "skip": skip,
        "limit": limit
    }
