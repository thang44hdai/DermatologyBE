from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import HTTPException

from app.models.database import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password


class UserService:
    """Service for user-related operations"""
    
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """
        Create a new user
        
        Args:
            db: Database session
            user: User creation data
            
        Returns:
            Created user object
        """
        # Check if user already exists
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        
        # Create new user
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password,
            full_name=user.full_name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get list of users"""
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete a user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.delete(user)
        db.commit()
        return True
