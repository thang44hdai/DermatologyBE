from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User role enum"""
    USER = "user"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str
    fullname: Optional[str] = None
    gender: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[datetime] = None


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")


class UserResponse(UserBase):
    """Response schema for user"""
    id: int
    role: UserRole
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Authentication Schemas
class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")


class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str = Field(..., description="Refresh token to get new access token")


class TokenData(BaseModel):
    """Schema for token data"""
    username: Optional[str] = None
    user_id: Optional[int] = None


class UserInDB(UserBase):
    """Schema for user in database (with hashed password)"""
    id: int
    password: str
    role: UserRole
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    """Schema for updating user role (admin only)"""
    role: UserRole = Field(..., description="New role for the user")
