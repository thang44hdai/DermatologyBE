from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Tuple, Optional

from app.models.database import Disease, Symptoms, Medicines, DiagnosisHistory
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
        Get disease with related counts
        
        Args:
            db: Database session
            disease_id: Disease ID
            
        Returns:
            Dict with disease and related counts
        """
        disease = db.query(Disease).filter(Disease.id == disease_id).first()
        
        if not disease:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Disease not found"
            )
        
        # Count related records
        symptoms_count = db.query(Symptoms).filter(Symptoms.disease_id == disease_id).count()
        medicines_count = db.query(Medicines).filter(Medicines.disease_id == disease_id).count()
        diagnosis_count = db.query(DiagnosisHistory).filter(DiagnosisHistory.disease_id == disease_id).count()
        
        return {
            "id": disease.id,
            "disease_name": disease.disease_name,
            "description": disease.description,
            "treatment": disease.treatment,
            "image_url": disease.image_url,
            "created_at": disease.created_at,
            "symptoms_count": symptoms_count,
            "medicines_count": medicines_count,
            "diagnosis_count": diagnosis_count
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
        
        # Check if disease has related records
        symptoms_count = db.query(Symptoms).filter(Symptoms.disease_id == disease_id).count()
        medicines_count = db.query(Medicines).filter(Medicines.disease_id == disease_id).count()
        diagnosis_count = db.query(DiagnosisHistory).filter(DiagnosisHistory.disease_id == disease_id).count()
        
        if symptoms_count > 0 or medicines_count > 0 or diagnosis_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete disease. It has {symptoms_count} symptoms, {medicines_count} medicines, and {diagnosis_count} diagnosis records. Remove related records first."
            )
        
        db.delete(disease)
        db.commit()
        return True


# Global service instance
disease_service = DiseaseService()
