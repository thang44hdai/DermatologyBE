from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import HTTPException, status
import json

from app.models.database import Pharmacies
from app.schemas.pharmacy import PharmacyCreate, PharmacyUpdate


class PharmacyService:
    """Service for pharmacy-related operations"""
    
    @staticmethod
    def create_pharmacy(db: Session, pharmacy: PharmacyCreate) -> Pharmacies:
        """
        Create a new pharmacy
        
        Args:
            db: Database session
            pharmacy: Pharmacy creation data
            
        Returns:
            Created pharmacy object
        """
        # Check if pharmacy with same name and address already exists
        existing = db.query(Pharmacies).filter(
            Pharmacies.name == pharmacy.name,
            Pharmacies.address == pharmacy.address
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pharmacy with this name and address already exists"
            )
        
        # Prepare image URLs as JSON if provided
        image_urls_json = None
        if pharmacy.images:
            image_urls_json = json.dumps(pharmacy.images)
        
        # Create new pharmacy
        db_pharmacy = Pharmacies(
            name=pharmacy.name,
            address=pharmacy.address,
            phone=pharmacy.phone,
            open_hours=pharmacy.open_hours,
            ratings=pharmacy.ratings,
            latitude=pharmacy.latitude,
            longitude=pharmacy.longitude,
            image_url=image_urls_json
        )
        
        db.add(db_pharmacy)
        db.commit()
        db.refresh(db_pharmacy)
        return db_pharmacy
    
    @staticmethod
    def get_pharmacy(db: Session, pharmacy_id: int) -> Optional[Pharmacies]:
        """Get pharmacy by ID"""
        pharmacy = db.query(Pharmacies).filter(Pharmacies.id == pharmacy_id).first()
        if not pharmacy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pharmacy not found"
            )
        return pharmacy
    
    @staticmethod
    def get_pharmacies(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> tuple[List[Pharmacies], int]:
        """
        Get list of pharmacies with optional search
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            search: Optional search term for name or address
            
        Returns:
            Tuple of (list of pharmacies, total count)
        """
        query = db.query(Pharmacies)
        
        # Apply search filter if provided
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Pharmacies.name.ilike(search_filter)) |
                (Pharmacies.address.ilike(search_filter))
            )
        
        total = query.count()
        pharmacies = query.offset(skip).limit(limit).all()
        
        return pharmacies, total
    
    @staticmethod
    def update_pharmacy(
        db: Session,
        pharmacy_id: int,
        pharmacy_update: PharmacyUpdate,
        new_images: List[str] = None,
        keep_existing_images: bool = True
    ) -> Pharmacies:
        """
        Update pharmacy information
        
        Args:
            db: Database session
            pharmacy_id: Pharmacy ID to update
            pharmacy_update: Updated pharmacy data
            new_images: List of new image URLs to add
            keep_existing_images: Whether to keep existing images
            
        Returns:
            Updated pharmacy object
        """
        pharmacy = db.query(Pharmacies).filter(Pharmacies.id == pharmacy_id).first()
        
        if not pharmacy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pharmacy not found"
            )
        
        # Update only provided fields
        update_data = pharmacy_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(pharmacy, field, value)
        
        # Handle images
        if new_images:
            existing_images = []
            if keep_existing_images and pharmacy.image_url:
                try:
                    existing_images = json.loads(pharmacy.image_url)
                except:
                    existing_images = []
            
            # Combine existing and new images
            all_images = existing_images + new_images
            pharmacy.image_url = json.dumps(all_images)
        
        db.commit()
        db.refresh(pharmacy)
        return pharmacy
    
    @staticmethod
    def delete_pharmacy(db: Session, pharmacy_id: int) -> bool:
        """
        Delete a pharmacy
        
        Args:
            db: Database session
            pharmacy_id: Pharmacy ID to delete
            
        Returns:
            True if deleted successfully
        """
        pharmacy = db.query(Pharmacies).filter(Pharmacies.id == pharmacy_id).first()
        
        if not pharmacy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pharmacy not found"
            )
        
        db.delete(pharmacy)
        db.commit()
        return True
    
    @staticmethod
    def search_nearby_pharmacies(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        limit: int = 20
    ) -> List[dict]:
        """
        Search for pharmacies near a location with distance calculation
        
        Args:
            db: Database session
            latitude: User's latitude
            longitude: User's longitude
            radius_km: Search radius in kilometers
            limit: Maximum number of results
            
        Returns:
            List of dictionaries with pharmacy data and distance_km
        """
        import math
        
        def haversine_distance(lat1, lon1, lat2, lon2):
            """
            Calculate the great circle distance between two points 
            on the earth (specified in decimal degrees)
            Returns distance in kilometers
            """
            # Convert decimal degrees to radians
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            # Radius of earth in kilometers
            r = 6371
            return c * r
        
        # Filter pharmacies that have coordinates
        pharmacies = db.query(Pharmacies).filter(
            Pharmacies.latitude.isnot(None),
            Pharmacies.longitude.isnot(None)
        ).all()
        
        # Calculate distance for each pharmacy
        nearby = []
        for pharmacy in pharmacies:
            distance = haversine_distance(
                latitude, longitude,
                pharmacy.latitude, pharmacy.longitude
            )
            
            # Filter by radius and add to results
            if distance <= radius_km:
                nearby.append({
                    "pharmacy": pharmacy,
                    "distance_km": round(distance, 2)
                })
        
        # Sort by distance (closest first)
        nearby.sort(key=lambda x: x["distance_km"])
        
        # Limit results
        return nearby[:limit]


# Global service instance
pharmacy_service = PharmacyService()
