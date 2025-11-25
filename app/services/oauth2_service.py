"""
OAuth2 Service

Service for handling Google and Facebook OAuth2 authentication for mobile apps.
Verifies ID tokens/access tokens and creates/links user accounts.
"""

import logging
import httpx
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from google.auth.transport import requests
from google.oauth2 import id_token

from app.config.settings import settings
from app.models.database import User
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


class OAuth2Service:
    """Service for OAuth2 authentication"""
    
    async def verify_google_id_token(self, token: str) -> dict:
        """
        Verify Google ID token from Android app
        
        Args:
            token: Google ID token from Sign-In SDK
            
        Returns:
            User info dict with keys: sub, email, name, picture
            
        Raises:
            ValueError: If token is invalid
        """
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
            
            # Validate issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer')
            
            logger.info(f"Google token verified for user: {idinfo.get('email')}")
            
            return {
                'sub': idinfo['sub'],  # Google user ID
                'email': idinfo['email'],
                'name': idinfo.get('name'),
                'picture': idinfo.get('picture')
            }
            
        except ValueError as e:
            logger.error(f"Google token verification failed: {e}")
            raise ValueError(f"Invalid Google ID token: {str(e)}")
    
    async def verify_facebook_token(self, access_token: str) -> dict:
        """
        Verify Facebook access token from Android app
        
        Args:
            access_token: Facebook access token from SDK
            
        Returns:
            User info dict with keys: id, email, name, picture
            
        Raises:
            ValueError: If token is invalid
        """
        try:
            async with httpx.AsyncClient() as client:
                # Verify token with Facebook Debug Token API
                debug_url = "https://graph.facebook.com/debug_token"
                debug_params = {
                    "input_token": access_token,
                    "access_token": f"{settings.FACEBOOK_APP_ID}|{settings.FACEBOOK_APP_SECRET}"
                }
                
                debug_response = await client.get(debug_url, params=debug_params)
                debug_data = debug_response.json()
                
                if not debug_data.get('data', {}).get('is_valid'):
                    raise ValueError("Invalid Facebook token")
                
                # Get user info
                user_url = "https://graph.facebook.com/me"
                user_params = {
                    "fields": "id,email,name,picture",
                    "access_token": access_token
                }
                
                user_response = await client.get(user_url, params=user_params)
                user_data = user_response.json()
                
                if 'error' in user_data:
                    raise ValueError(user_data['error'].get('message', 'Facebook API error'))
                
                logger.info(f"Facebook token verified for user: {user_data.get('email')}")
                
                return {
                    'id': user_data['id'],
                    'email': user_data.get('email'),
                    'name': user_data.get('name'),
                    'picture': user_data.get('picture', {}).get('data', {}).get('url')
                }
                
        except Exception as e:
            logger.error(f"Facebook token verification failed: {e}")
            raise ValueError(f"Invalid Facebook access token: {str(e)}")
    
    def get_or_create_oauth_user(
        self,
        db: Session,
        provider: str,
        oauth_id: str,
        email: Optional[str],
        name: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Tuple[User, bool]:
        """
        Get existing user or create new user from OAuth data
        
        Args:
            db: Database session
            provider: 'google' or 'facebook'
            oauth_id: OAuth provider's user ID
            email: User email
            name: User full name
            avatar_url: User avatar URL
            
        Returns:
            Tuple of (User, is_new_user)
            
        Raises:
            ValueError: If email is required but not provided
        """
        # Check if user with OAuth ID already exists
        if provider == 'google':
            user = db.query(User).filter(User.google_id == oauth_id).first()
        else:  # facebook
            user = db.query(User).filter(User.facebook_id == oauth_id).first()
        
        if user:
            logger.info(f"Existing {provider} user found: {user.email}")
            return user, False
        
        # Check if user with email exists (for linking)
        if email:
            user = db.query(User).filter(User.email == email).first()
            if user:
                # Link OAuth to existing account
                logger.info(f"Linking {provider} account to existing user: {email}")
                user.oauth_provider = provider
                if provider == 'google':
                    user.google_id = oauth_id
                else:
                    user.facebook_id = oauth_id
                
                # Update avatar if not set
                if avatar_url and not user.avatar_url:
                    user.avatar_url = avatar_url
                
                db.commit()
                db.refresh(user)
                return user, False
        
        # Create new user
        if not email:
            raise ValueError(f"Email is required for {provider} authentication")
        
        logger.info(f"Creating new {provider} user: {email}")
        
        # Generate username from email
        username = email.split('@')[0]
        # Ensure unique username
        base_username = username
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user
        user = User(
            email=email,
            username=username,
            password=get_password_hash("oauth_user_no_password"),  # Dummy password
            fullname=name,
            avatar_url=avatar_url,
            oauth_provider=provider,
            google_id=oauth_id if provider == 'google' else None,
            facebook_id=oauth_id if provider == 'facebook' else None
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"New {provider} user created: {email}")
        return user, True


# Singleton instance
oauth2_service = OAuth2Service()
