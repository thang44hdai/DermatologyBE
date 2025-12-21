from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_active_user
from app.core.security import (
    create_access_token, 
    create_refresh_token,
    decode_refresh_token
)
from app.schemas.user import (
    UserCreate, 
    UserResponse, 
    Token, 
    LoginRequest,
    RefreshTokenRequest
)
from app.schemas.oauth import GoogleAuthRequest, FacebookAuthRequest, OAuth2Response
from app.services.user_service import UserService
from app.services.oauth2_service import oauth2_service
from app.models import User
from app.config import settings

router = APIRouter(tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    
    - **email**: Valid email address
    - **username**: Unique username
    - **password**: Password (minimum 6 characters)
    - **fullname**: Optional full name
    - **gender**: Optional gender
    - **avatar_url**: Optional avatar URL
    - **date_of_birth**: Optional date of birth
    """
    return UserService.create_user(db=db, user=user)


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login - Use this with Swagger Authorize button
    
    Returns both access token and refresh token
    
    - **username**: Username or email
    - **password**: User password
    
    Returns:
    - **access_token**: Short-lived token for API access (30 minutes)
    - **refresh_token**: Long-lived token for getting new access tokens (7 days)
    """
    user = UserService.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=Token)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with JSON credentials (alternative to /token)
    
    Returns both access token and refresh token
    
    - **username**: Username or email
    - **password**: User password
    
    Returns:
    - **access_token**: Short-lived token for API access (30 minutes)
    - **refresh_token**: Long-lived token for getting new access tokens (7 days)
    """
    user = UserService.authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Get new access token using refresh token
    
    When your access token expires, use this endpoint with your refresh token
    to get a new pair of tokens
    
    - **refresh_token**: Your valid refresh token
    
    Returns:
    - **access_token**: New access token (30 minutes)
    - **refresh_token**: New refresh token (7 days)
    """
    # Decode and verify refresh token
    payload = decode_refresh_token(refresh_data.refresh_token)
    
    username: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user still exists and is active
    user = UserService.get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    new_refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information
    
    Requires authentication token
    """
    return current_user


@router.get("/test-token")
async def test_token(current_user: User = Depends(get_current_active_user)):
    """
    Test access token
    
    This endpoint can be used to verify if your token is valid
    """
    return {
        "message": "Token is valid",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email
        }
    }


# ===== OAuth2 Endpoints for Mobile =====

@router.post("/google", response_model=OAuth2Response)
async def google_auth(
    request: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate with Google ID token from Android app
    
    Android app flow:
    1. Use Google Sign-In SDK to get ID token
    2. Send ID token to this endpoint
    3. Backend verifies token and returns JWT
    
    Args:
        id_token: Google ID token from Android SDK
        
    Returns:
        JWT access token, user info, and is_new_user flag
    """
    # Verify Google ID token
    try:
        user_info = await oauth2_service.verify_google_id_token(request.id_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    
    # Get or create user
    user, is_new = oauth2_service.get_or_create_oauth_user(
        db=db,
        provider="google",
        oauth_id=user_info["sub"],
        email=user_info.get("email"),
        name=user_info.get("name"),
        avatar_url=user_info.get("picture")
    )
    
    # Generate JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return OAuth2Response(
        access_token=access_token,
        token_type="bearer",
        user=user,
        is_new_user=is_new
    )


@router.post("/facebook", response_model=OAuth2Response)  
async def facebook_auth(
    request: FacebookAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate with Facebook access token from Android app
    
    Android app flow:
    1. Use Facebook SDK to get access token
    2. Send token to this endpoint
    3. Backend verifies token and returns JWT
    
    Args:
        access_token: Facebook access token from Android SDK
        
    Returns:
        JWT access token, user info, and is_new_user flag
    """
    # Verify Facebook token
    try:
        user_info = await oauth2_service.verify_facebook_token(request.access_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    
    # Get or create user
    user, is_new = oauth2_service.get_or_create_oauth_user(
        db=db,
        provider="facebook",
        oauth_id=user_info["id"],
        email=user_info.get("email"),
        name=user_info.get("name"),
        avatar_url=user_info.get("picture")
    )
    
    # Generate JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return OAuth2Response(
        access_token=access_token,
        token_type="bearer",
        user=user,
        is_new_user=is_new
    )
