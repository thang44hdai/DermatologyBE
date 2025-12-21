from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import HTTPException, status

from app.models import User, UserRole
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password


class UserService:
    """Service for user-related operations"""
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username/email and password
        
        Args:
            db: Database session
            username: Username or email
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        # Try to find user by username or email
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            return None
        
        if not verify_password(password, user.password):
            return None
        
        return user
    
    @staticmethod
    def create_user(db: Session, user: UserCreate, role: UserRole = UserRole.USER) -> User:
        """
        Create a new user
        
        Args:
            db: Database session
            user: User creation data
            role: User role (default: USER)
            
        Returns:
            Created user object
        """
        # Check if user already exists
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            username=user.username,
            password=hashed_password,
            fullname=user.fullname,
            role=role,  # Set role (default is USER)
            gender=user.gender,
            avatar_url=user.avatar_url,
            date_of_birth=user.date_of_birth
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
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get list of users"""
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Delete a user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        db.delete(user)
        db.commit()
        return True
    
    @staticmethod
    def update_user_role(db: Session, user_id: int, new_role: UserRole) -> User:
        """
        Update user role (admin only operation)
        
        Args:
            db: Database session
            user_id: User ID to update
            new_role: New role to assign
            
        Returns:
            Updated user object
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.role = new_role
        db.commit()
        db.refresh(user)
        return user
