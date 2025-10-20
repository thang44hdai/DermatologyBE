from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter()


@router.post("/", response_model=UserResponse, tags=["Users"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user
    """
    return UserService.create_user(db=db, user=user)


@router.get("/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get user by ID
    """
    db_user = UserService.get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.get("/", response_model=List[UserResponse], tags=["Users"])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get list of users
    """
    users = UserService.get_users(db=db, skip=skip, limit=limit)
    return users


@router.delete("/{user_id}", tags=["Users"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete a user
    """
    UserService.delete_user(db=db, user_id=user_id)
    return {"message": "User deleted successfully"}
