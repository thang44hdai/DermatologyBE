from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str


class UserResponse(UserBase):
    """Response schema for user"""
    id: int
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True
