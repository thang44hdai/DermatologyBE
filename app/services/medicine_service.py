from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Tuple, Optional
import json

from app.models import Medicines, Pharmacies, MedicinePharmacyLink, Disease, MedicineDiseaseLink
from app.schemas.medicine import (
    MedicineCreate,
    MedicineUpdate,
    MedicinePharmacyLinkCreate,
    MedicinePharmacyLinkUpdate
)


class MedicineService:
    """Service for medicine management"""
    
    @staticmethod
    def create_medicine(db: Session, medicine: MedicineCreate, image_urls: Optional[List[str]] = None) -> Medicines:
        """
        Create a new medicine
        
        Args:
            db: Database session
            medicine: Medicine data
            image_urls: List of image URLs to store as JSON
            
        Returns:
            Created medicine object
        """
        # Check if all diseases exist
        for disease_id in medicine.disease_ids:
            disease = db.query(Disease).filter(Disease.id == disease_id).first()
            if not disease:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Disease with ID {disease_id} not found"
                )
        
        # Check for duplicate medicine name
        existing = db.query(Medicines).filter(Medicines.name == medicine.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Medicine '{medicine.name}' already exists"
            )
        
        # Prepare medicine data (exclude disease_ids as it's not a direct column)
        medicine_data = medicine.model_dump(exclude={"images", "disease_ids"})
        
        # Add images as JSON string
        if image_urls:
            medicine_data["image_url"] = json.dumps(image_urls)
        else:
            medicine_data["image_url"] = None
        
        # Create medicine
        db_medicine = Medicines(**medicine_data)
        db.add(db_medicine)
        db.flush()  # Get the medicine ID without committing
        
        # Create medicine-disease links
        for disease_id in medicine.disease_ids:
            link = MedicineDiseaseLink(
                medicine_id=db_medicine.id,
                disease_id=disease_id
            )
            db.add(link)
        
        db.commit()
        db.refresh(db_medicine)
        return db_medicine
    
    @staticmethod
    def get_medicine(db: Session, medicine_id: int) -> Medicines:
        """
        Get medicine by ID
        
        Args:
            db: Database session
            medicine_id: Medicine ID
            
        Returns:
            Medicine object
        """
        medicine = db.query(Medicines).filter(Medicines.id == medicine_id).first()
        
        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medicine not found"
            )
        
        return medicine
    
    @staticmethod
    def get_medicines(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        disease_id: Optional[int] = None,
        medicine_type: Optional[str] = None
    ) -> Tuple[List[Medicines], int]:
        """
        Get list of medicines with filters
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records
            search: Search term for name or generic name
            disease_id: Filter by disease ID (searches in medicine-disease links)
            medicine_type: Filter by medicine type
            
        Returns:
            Tuple of (list of medicines, total count)
        """
        query = db.query(Medicines)
        
        # Apply filters
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Medicines.name.ilike(search_filter)) |
                (Medicines.generic_name.ilike(search_filter))
            )
        
        if disease_id:
            # Filter by disease through the many-to-many relationship
            query = query.join(MedicineDiseaseLink).filter(MedicineDiseaseLink.disease_id == disease_id)
        
        if medicine_type:
            query = query.filter(Medicines.type.ilike(f"%{medicine_type}%"))
        
        total = query.count()
        medicines = query.offset(skip).limit(limit).all()
        
        return medicines, total
    
    @staticmethod
    def update_medicine(
        db: Session,
        medicine_id: int,
        medicine_update: MedicineUpdate,
        image_urls: Optional[List[str]] = None
    ) -> Medicines:
        """
        Update medicine information
        
        Args:
            db: Database session
            medicine_id: Medicine ID to update
            medicine_update: Updated medicine data
            image_urls: List of image URLs to store as JSON (if provided)
            
        Returns:
            Updated medicine object
        """
        medicine = db.query(Medicines).filter(Medicines.id == medicine_id).first()
        
        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medicine not found"
            )
        
        # Update only provided fields
        update_data = medicine_update.model_dump(exclude_unset=True, exclude={"images", "disease_ids"})
        
        # Handle disease_ids update
        if medicine_update.disease_ids is not None:
            # Check if all diseases exist
            for disease_id in medicine_update.disease_ids:
                disease = db.query(Disease).filter(Disease.id == disease_id).first()
                if not disease:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Disease with ID {disease_id} not found"
                    )
            
            # Remove existing disease links
            db.query(MedicineDiseaseLink).filter(MedicineDiseaseLink.medicine_id == medicine_id).delete()
            
            # Create new disease links
            for disease_id in medicine_update.disease_ids:
                link = MedicineDiseaseLink(
                    medicine_id=medicine_id,
                    disease_id=disease_id
                )
                db.add(link)
        
        # Handle images update
        if image_urls is not None:
            update_data["image_url"] = json.dumps(image_urls) if image_urls else None
        
        for field, value in update_data.items():
            setattr(medicine, field, value)
        
        db.commit()
        db.refresh(medicine)
        return medicine
    
    @staticmethod
    def delete_medicine(db: Session, medicine_id: int) -> bool:
        """
        Delete a medicine
        
        Args:
            db: Database session
            medicine_id: Medicine ID to delete
            
        Returns:
            True if deleted successfully
        """
        medicine = db.query(Medicines).filter(Medicines.id == medicine_id).first()
        
        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medicine not found"
            )
        
        # Check if medicine is linked to any pharmacies
        links = db.query(MedicinePharmacyLink).filter(
            MedicinePharmacyLink.medicine_id == medicine_id
        ).count()
        
        if links > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete medicine. It is linked to {links} pharmacy/pharmacies. Remove links first."
            )
        
        db.delete(medicine)
        db.commit()
        return True
    
    # ===== Medicine-Pharmacy Link Management =====
    
    @staticmethod
    def add_medicine_to_pharmacy(
        db: Session,
        link: MedicinePharmacyLinkCreate
    ) -> MedicinePharmacyLink:
        """
        Add medicine to a pharmacy (create link)
        
        Args:
            db: Database session
            link: Medicine-pharmacy link data
            
        Returns:
            Created link object
        """
        # Check if medicine exists
        medicine = db.query(Medicines).filter(Medicines.id == link.medicine_id).first()
        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medicine with ID {link.medicine_id} not found"
            )
        
        # Check if pharmacy exists
        pharmacy = db.query(Pharmacies).filter(Pharmacies.id == link.pharmacy_id).first()
        if not pharmacy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pharmacy with ID {link.pharmacy_id} not found"
            )
        
        # Check if link already exists
        existing_link = db.query(MedicinePharmacyLink).filter(
            MedicinePharmacyLink.medicine_id == link.medicine_id,
            MedicinePharmacyLink.pharmacy_id == link.pharmacy_id
        ).first()
        
        if existing_link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Medicine '{medicine.name}' is already linked to pharmacy '{pharmacy.name}'"
            )
        
        db_link = MedicinePharmacyLink(**link.model_dump())
        db.add(db_link)
        db.commit()
        db.refresh(db_link)
        return db_link
    
    @staticmethod
    def update_medicine_pharmacy_link(
        db: Session,
        link_id: int,
        link_update: MedicinePharmacyLinkUpdate
    ) -> MedicinePharmacyLink:
        """
        Update medicine-pharmacy link (stock, price)
        
        Args:
            db: Database session
            link_id: Link ID
            link_update: Updated link data
            
        Returns:
            Updated link object
        """
        link = db.query(MedicinePharmacyLink).filter(MedicinePharmacyLink.id == link_id).first()
        
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medicine-pharmacy link not found"
            )
        
        update_data = link_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(link, field, value)
        
        db.commit()
        db.refresh(link)
        return link
    
    @staticmethod
    def remove_medicine_from_pharmacy(
        db: Session,
        link_id: int
    ) -> bool:
        """
        Remove medicine from pharmacy (delete link)
        
        Args:
            db: Database session
            link_id: Link ID to delete
            
        Returns:
            True if deleted successfully
        """
        link = db.query(MedicinePharmacyLink).filter(MedicinePharmacyLink.id == link_id).first()
        
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medicine-pharmacy link not found"
            )
        
        db.delete(link)
        db.commit()
        return True
    
    @staticmethod
    def get_pharmacy_medicines(
        db: Session,
        pharmacy_id: int,
        skip: int = 0,
        limit: int = 50
    ):
        """
        Get all medicines available at a specific pharmacy
        
        Args:
            db: Database session
            pharmacy_id: Pharmacy ID
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Dict with pharmacy info and medicines list
        """
        # Check if pharmacy exists
        pharmacy = db.query(Pharmacies).filter(Pharmacies.id == pharmacy_id).first()
        if not pharmacy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pharmacy not found"
            )
        
        # Get medicines at this pharmacy
        query = db.query(
            MedicinePharmacyLink,
            Medicines
        ).join(
            Medicines, MedicinePharmacyLink.medicine_id == Medicines.id
        ).filter(
            MedicinePharmacyLink.pharmacy_id == pharmacy_id
        )
        
        total = query.count()
        results = query.offset(skip).limit(limit).all()
        
        medicines = []
        for link, medicine in results:
            # Parse images from JSON
            images = None
            if medicine.image_url:
                try:
                    images = json.loads(medicine.image_url)
                except:
                    if medicine.image_url:
                        images = [medicine.image_url]
            
            medicines.append({
                "link_id": link.id,
                "medicine_id": medicine.id,
                "medicine_name": medicine.name,
                "generic_name": medicine.generic_name,
                "type": medicine.type,
                "dosage": medicine.dosage,
                "description": medicine.description,
                "side_effects": medicine.side_effects,
                "suitable_for": medicine.suitable_for,
                "images": images,
                "stock": link.stock,
                "price": link.price,
                "last_updated": link.last_updated
            })
        
        return {
            "pharmacy_id": pharmacy.id,
            "pharmacy_name": pharmacy.name,
            "medicines": medicines,
            "total": total
        }
    
    @staticmethod
    def get_medicine_availability(
        db: Session,
        medicine_id: int
    ):
        """
        Get all pharmacies where a medicine is available
        
        Args:
            db: Database session
            medicine_id: Medicine ID
            
        Returns:
            Dict with medicine info and pharmacy availability list
        """
        # Check if medicine exists
        medicine = db.query(Medicines).filter(Medicines.id == medicine_id).first()
        if not medicine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Medicine not found"
            )
        
        # Get pharmacies that have this medicine
        results = db.query(
            MedicinePharmacyLink,
            Pharmacies
        ).join(
            Pharmacies, MedicinePharmacyLink.pharmacy_id == Pharmacies.id
        ).filter(
            MedicinePharmacyLink.medicine_id == medicine_id
        ).all()
        
        pharmacies = []
        for link, pharmacy in results:
            pharmacies.append({
                "link_id": link.id,
                "pharmacy_id": pharmacy.id,
                "pharmacy_name": pharmacy.name,
                "pharmacy_address": pharmacy.address,
                "pharmacy_phone": pharmacy.phone,
                "pharmacy_ratings": pharmacy.ratings,
                "stock": link.stock,
                "price": link.price,
                "last_updated": link.last_updated
            })
        
        return {
            "medicine_id": medicine.id,
            "medicine_name": medicine.name,
            "generic_name": medicine.generic_name,
            "pharmacies": pharmacies,
            "total_pharmacies": len(pharmacies)
        }


# Global service instance
medicine_service = MedicineService()
