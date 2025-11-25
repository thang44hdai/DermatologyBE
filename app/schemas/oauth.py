"""
OAuth2 Schemas

Pydantic models for OAuth2 authentication with Google and Facebook.
"""

from pydantic import BaseModel, Field
from app.schemas.user import UserResponse


class GoogleAuthRequest(BaseModel):
    """Request from Android app with Google ID token"""
    id_token: str = Field(
        ..., 
        description="Google ID token from Android Sign-In SDK",
        min_length=1
    )


class FacebookAuthRequest(BaseModel):
    """Request from Android app with Facebook access token"""
    access_token: str = Field(
        ...,
        description="Facebook access token from Android SDK",
        min_length=1
    )


class OAuth2Response(BaseModel):
    """Response after successful OAuth authentication"""
    access_token: str = Field(..., description="JWT access token for API authentication")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")
    is_new_user: bool = Field(..., description="True if this is a newly created account")
