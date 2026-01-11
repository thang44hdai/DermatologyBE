from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Tuple, Optional
import json

from app.models import Disease, Medicines, DiagnosisHistory, MedicineDiseaseLink
from app.schemas.disease import DiseaseCreate, DiseaseUpdate


class DiseaseService:
    """Service for disease management"""
    
    @staticmethod
    def create_disease(db: Session, disease: DiseaseCreate) -> Disease:
        """
        Create a new disease
        
        Args:
            db: Database session
            disease: Disease data
            
        Returns:
            Created disease object
        """
        # Check for duplicate disease name
        existing = db.query(Disease).filter(
            Disease.disease_name == disease.disease_name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Disease '{disease.disease_name}' already exists"
            )
        
        db_disease = Disease(**disease.model_dump())
        db.add(db_disease)
        db.commit()
        db.refresh(db_disease)
        return db_disease
    
    @staticmethod
    def get_disease(db: Session, disease_id: int) -> Disease:
        """
        Get disease by ID
        
        Args:
            db: Database session
            disease_id: Disease ID
            
        Returns:
            Disease object
        """
        disease = db.query(Disease).filter(Disease.id == disease_id).first()
        
        if not disease:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Disease not found"
            )
        
        return disease
    
    @staticmethod
    def get_disease_detail(db: Session, disease_id: int) -> dict:
        """
        Get disease with related counts and medicines
        
        Args:
            db: Database session
            disease_id: Disease ID
            
        Returns:
            Dict with disease and related counts and medicines
        """
        disease = db.query(Disease).filter(Disease.id == disease_id).first()
        
        if not disease:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Disease not found"
            )
        
        # Get medicines for this disease via many-to-many relationship
        medicines = db.query(Medicines).join(
            MedicineDiseaseLink,
            Medicines.id == MedicineDiseaseLink.medicine_id
        ).filter(
            MedicineDiseaseLink.disease_id == disease_id
        ).all()
        
        # Count diagnosis records
        diagnosis_count = db.query(DiagnosisHistory).filter(
            DiagnosisHistory.disease_id == disease_id
        ).count()
        
        # Parse image_url JSON for each medicine
        medicines_list = []
        for med in medicines:
            # Parse image_url from JSON array to get first image
            first_image = None
            if med.image_url:
                try:
                    images = json.loads(med.image_url)
                    if images and isinstance(images, list) and len(images) > 0:
                        first_image = images[0]
                except json.JSONDecodeError:
                    first_image = med.image_url  # Fallback to raw value
            
            medicines_list.append({
                "id": med.id,
                "name": med.name,
                "generic_name": med.generic_name,
                "type": med.type,
                "price": med.price,
                "image_url": first_image
            })
        
        return {
            "id": disease.id,
            "disease_name": disease.disease_name,
            "description": disease.description,
            "symptoms": disease.symptoms,
            "treatment": disease.treatment,
            "image_url": disease.image_url,
            "created_at": disease.created_at,
            "medicines_count": len(medicines_list),
            "diagnosis_count": diagnosis_count,
            "medicines": medicines_list
        }
    
    @staticmethod
    def get_diseases(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None
    ) -> Tuple[List[Disease], int]:
        """
        Get list of diseases with search
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records
            search: Search term for disease name
            
        Returns:
            Tuple of (list of diseases, total count)
        """
        query = db.query(Disease)
        
        # Apply search filter
        if search:
            search_filter = f"%{search}%"
            query = query.filter(Disease.disease_name.ilike(search_filter))
        
        total = query.count()
        diseases = query.offset(skip).limit(limit).all()
        
        return diseases, total
    
    @staticmethod
    def get_diseases_with_medicines(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        """
        Get list of diseases with medicines
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records
            search: Search term for disease name
            
        Returns:
            Tuple of (list of disease dicts with medicines, total count)
        """
        query = db.query(Disease)
        
        # Apply search filter
        if search:
            search_filter = f"%{search}%"
            query = query.filter(Disease.disease_name.ilike(search_filter))
        
        total = query.count()
        diseases = query.offset(skip).limit(limit).all()
        
        # Build response with medicines for each disease
        result = []
        for disease in diseases:
            # Get medicines for this disease
            medicines = db.query(Medicines).join(
                MedicineDiseaseLink,
                Medicines.id == MedicineDiseaseLink.medicine_id
            ).filter(
                MedicineDiseaseLink.disease_id == disease.id
            ).all()
            
            # Count diagnosis records
            diagnosis_count = db.query(DiagnosisHistory).filter(
                DiagnosisHistory.disease_id == disease.id
            ).count()
            
            # Parse image_url JSON for each medicine
            medicines_list = []
            for med in medicines:
                first_image = None
                if med.image_url:
                    try:
                        images = json.loads(med.image_url)
                        if images and isinstance(images, list) and len(images) > 0:
                            first_image = images[0]
                    except json.JSONDecodeError:
                        first_image = med.image_url
                
                medicines_list.append({
                    "id": med.id,
                    "name": med.name,
                    "generic_name": med.generic_name,
                    "type": med.type,
                    "price": med.price,
                    "image_url": first_image
                })
            
            result.append({
                "id": disease.id,
                "disease_name": disease.disease_name,
                "description": disease.description,
                "symptoms": disease.symptoms,
                "treatment": disease.treatment,
                "image_url": disease.image_url,
                "created_at": disease.created_at,
                "medicines_count": len(medicines_list),
                "diagnosis_count": diagnosis_count,
                "medicines": medicines_list
            })
        
        return result, total
    
    @staticmethod
    def update_disease(
        db: Session,
        disease_id: int,
        disease_update: DiseaseUpdate
    ) -> Disease:
        """
        Update disease information
        
        Args:
            db: Database session
            disease_id: Disease ID to update
            disease_update: Updated disease data
            
        Returns:
            Updated disease object
        """
        disease = db.query(Disease).filter(Disease.id == disease_id).first()
        
        if not disease:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Disease not found"
            )
        
        # Update only provided fields
        update_data = disease_update.model_dump(exclude_unset=True)
        
        # Check for duplicate name if name is being updated
        if "disease_name" in update_data:
            existing = db.query(Disease).filter(
                Disease.disease_name == update_data["disease_name"],
                Disease.id != disease_id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Disease '{update_data['disease_name']}' already exists"
                )
        
        for field, value in update_data.items():
            setattr(disease, field, value)
        
        db.commit()
        db.refresh(disease)
        return disease
    
    @staticmethod
    def delete_disease(db: Session, disease_id: int) -> bool:
        """
        Delete a disease
        
        Args:
            db: Database session
            disease_id: Disease ID to delete
            
        Returns:
            True if deleted successfully
        """
        disease = db.query(Disease).filter(Disease.id == disease_id).first()
        
        if not disease:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Disease not found"
            )
        
        # Check if disease has related records via many-to-many relationship
        medicines_count = db.query(MedicineDiseaseLink).filter(
            MedicineDiseaseLink.disease_id == disease_id
        ).count()
        
        diagnosis_count = db.query(DiagnosisHistory).filter(
            DiagnosisHistory.disease_id == disease_id
        ).count()
        
        if medicines_count > 0 or diagnosis_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete disease. It has {medicines_count} medicines and {diagnosis_count} diagnosis records. Remove related records first."
            )
        
        db.delete(disease)
        db.commit()
        return True


# Global service instance
disease_service = DiseaseService()
