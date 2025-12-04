from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.database import Category, Medicines
from app.schemas.category import CategoryCreate, CategoryUpdate
from fastapi import HTTPException, status
from typing import Optional


class CategoryService:
    
    @staticmethod
    def create_category(db: Session, data: CategoryCreate) -> Category:
        """Create a new category"""
        # Check duplicate name
        existing = db.query(Category).filter(Category.name == data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{data.name}' already exists"
            )
        
        category = Category(**data.model_dump())
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def get_all_categories(
        db: Session, 
        skip: int = 0, 
        limit: int = 50,
        is_active: Optional[bool] = None,
        include_count: bool = False
    ):
        """Get all categories with optional filtering"""
        query = db.query(Category)
        
        if is_active is not None:
            query = query.filter(Category.is_active == is_active)
        
        query = query.order_by(Category.name)
        categories = query.offset(skip).limit(limit).all()
        
        if include_count:
            for cat in categories:
                cat.medicine_count = db.query(Medicines).filter(
                    Medicines.category_id == cat.id
                ).count()
        
        return categories
    
    @staticmethod
    def get_category(db: Session, category_id: int) -> Category:
        """Get a single category by ID"""
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        return category
    
    @staticmethod
    def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Category:
        """Update a category"""
        category = CategoryService.get_category(db, category_id)
        
        update_dict = data.model_dump(exclude_unset=True)
        
        # Check for name conflict if name is being updated
        if 'name' in update_dict and update_dict['name'] != category.name:
            existing = db.query(Category).filter(Category.name == update_dict['name']).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category '{update_dict['name']}' already exists"
                )
        
        for field, value in update_dict.items():
            setattr(category, field, value)
        
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def delete_category(db: Session, category_id: int):
        """Soft delete a category"""
        category = CategoryService.get_category(db, category_id)
        
        # Soft delete
        category.is_active = False
        
        # Remove category from medicines
        db.query(Medicines).filter(
            Medicines.category_id == category_id
        ).update({"category_id": None})
        
        db.commit()
        return {"message": "Category deleted successfully"}
    
    @staticmethod
    def get_medicines_by_category(
        db: Session,
        category_id: int,
        skip: int = 0,
        limit: int = 50
    ):
        """Get all medicines in a category"""
        category = CategoryService.get_category(db, category_id)
        
        medicines = db.query(Medicines).filter(
            Medicines.category_id == category_id
        ).offset(skip).limit(limit).all()
        
        total = db.query(Medicines).filter(Medicines.category_id == category_id).count()
        
        return {
            "category": category,
            "medicines": medicines,
            "total": total
        }


# Singleton instance
category_service = CategoryService()
