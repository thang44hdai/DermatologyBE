from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db, get_current_active_user, get_current_admin
from app.schemas.user import UserCreate, UserResponse, UserRoleUpdate
from app.services.user_service import UserService
from app.models.database import User

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user (Public endpoint for registration)
    
    Note: For authenticated registration, use /api/v1/auth/register
    New users get 'user' role by default
    """
    return UserService.create_user(db=db, user=user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user by ID (Protected - requires authentication)
    
    Users can view their own profile or any profile if they're logged in
    """
    db_user = UserService.get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user


@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)  # Admin only
):
    """
    Get list of users (Protected - Admin only)
    
    Only administrators can view the full list of users
    """
    users = UserService.get_users(db=db, skip=skip, limit=limit)
    return users


@router.delete("/{user_id}")
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a user (Protected)
    
    - Users can delete their own account
    - Admins can delete any account
    """
    # Check if user is admin or deleting their own account
    from app.models.database import UserRole
    
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user. You can only delete your own account."
        )
    
    UserService.delete_user(db=db, user_id=user_id)
    return {"message": "User deleted successfully"}


@router.put("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)  # Admin only
):
    """
    Update user role (Protected - Admin only)
    
    Only administrators can promote/demote users
    
    - **role**: 'user' or 'admin'
    """
    # Prevent admin from demoting themselves
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role"
        )
    
    updated_user = UserService.update_user_role(db, user_id, role_update.role)
    return updated_user
