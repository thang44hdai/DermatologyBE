from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.dependencies import get_db, get_current_admin
from app.services.pharmacy_service import pharmacy_service
from app.schemas.pharmacy import (
    PharmacyCreate,
    PharmacyUpdate,
    PharmacyResponse,
    PharmacyListResponse,
    PharmacyWithDistanceResponse
)
from app.models.database import User

router = APIRouter()


@router.post("/", response_model=PharmacyResponse, status_code=status.HTTP_201_CREATED)
async def create_pharmacy(
    pharmacy: PharmacyCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Create a new pharmacy
    
    **Requires Admin Role**
    
    Args:
        name: Pharmacy name (required)
        address: Pharmacy address (required)
        phone: Contact phone number (optional)
        open_hours: Opening hours (optional)
        ratings: Rating 0-5 (optional)
        latitude: Location latitude (optional)
        longitude: Location longitude (optional)
        
    Returns:
        Created pharmacy information
    """
    return pharmacy_service.create_pharmacy(db, pharmacy)


@router.get("/", response_model=PharmacyListResponse)
async def get_pharmacies(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records"),
    search: Optional[str] = Query(None, description="Search by name or address"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get list of all pharmacies with pagination and search
    
    **Requires Admin Role**
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (max 100)
        search: Optional search term for name or address
        
    Returns:
        List of pharmacies with pagination info
    """
    pharmacies, total = pharmacy_service.get_pharmacies(
        db=db,
        skip=skip,
        limit=limit,
        search=search
    )
    
    return {
        "pharmacies": pharmacies,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{pharmacy_id}", response_model=PharmacyResponse)
async def get_pharmacy(
    pharmacy_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Get pharmacy by ID
    
    **Requires Admin Role**
    
    Args:
        pharmacy_id: Pharmacy ID
        
    Returns:
        Pharmacy information
    """
    return pharmacy_service.get_pharmacy(db, pharmacy_id)


@router.put("/{pharmacy_id}", response_model=PharmacyResponse)
async def update_pharmacy(
    pharmacy_id: int,
    pharmacy_update: PharmacyUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Update pharmacy information
    
    **Requires Admin Role**
    
    Args:
        pharmacy_id: Pharmacy ID to update
        
    Body: Fields to update (all optional)
        - name: Pharmacy name
        - address: Pharmacy address
        - phone: Contact phone
        - open_hours: Opening hours
        - ratings: Rating 0-5
        - latitude: Location latitude
        - longitude: Location longitude
        
    Returns:
        Updated pharmacy information
    """
    return pharmacy_service.update_pharmacy(db, pharmacy_id, pharmacy_update)


@router.delete("/{pharmacy_id}")
async def delete_pharmacy(
    pharmacy_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Delete a pharmacy
    
    **Requires Admin Role**
    
    Args:
        pharmacy_id: Pharmacy ID to delete
        
    Returns:
        Success message
    """
    pharmacy_service.delete_pharmacy(db, pharmacy_id)
    
    return {
        "success": True,
        "message": "Pharmacy deleted successfully",
        "pharmacy_id": pharmacy_id
    }


@router.get("/nearby/search", response_model=list[PharmacyWithDistanceResponse])
async def search_nearby_pharmacies(
    latitude: float = Query(..., description="Your latitude coordinate"),
    longitude: float = Query(..., description="Your longitude coordinate"),
    radius_km: float = Query(5.0, ge=0.1, le=50, description="Search radius in kilometers"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Search for pharmacies near a location with distance calculation
    
    **Requires Admin Role**
    
    **Uses Haversine formula for accurate distance calculation**
    
    Args:
        latitude: Your latitude coordinate
        longitude: Your longitude coordinate
        radius_km: Search radius in kilometers (0.1-50, default 5)
        limit: Maximum number of results (1-100, default 20)
        
    Returns:
        List of nearby pharmacies sorted by distance (closest first)
        Each result includes distance_km field
    """
    nearby_results = pharmacy_service.search_nearby_pharmacies(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        limit=limit
    )
    
    # Convert to response format with distance
    response = []
    for result in nearby_results:
        pharmacy = result["pharmacy"]
        distance = result["distance_km"]
        
        response.append(PharmacyWithDistanceResponse(
            id=pharmacy.id,
            name=pharmacy.name,
            address=pharmacy.address,
            phone=pharmacy.phone,
            open_hours=pharmacy.open_hours,
            ratings=pharmacy.ratings,
            latitude=pharmacy.latitude,
            longitude=pharmacy.longitude,
            distance_km=distance
        ))
    
    return response
