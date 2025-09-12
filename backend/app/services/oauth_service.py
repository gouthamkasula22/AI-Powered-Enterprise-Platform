"""
OAuth Service

Handles OAuth 2.0 authentication with various providers (Google, GitHub, etc.)
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db_session
from app.models import User, SocialAccount
from app.core.security import create_access_token, create_refresh_token
from app.core.config import settings

logger = logging.getLogger(__name__)


class OAuthService:
    """OAuth 2.0 Service for handling third-party authentication"""
    
    # OAuth Provider configurations
    PROVIDERS = {
        'google': {
            'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
            'token_url': 'https://oauth2.googleapis.com/token',
            'userinfo_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
            'scope': 'openid email profile',
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI or 'http://localhost:8000/api/v1/auth/oauth/google/callback'
        },
        'github': {
            'auth_url': 'https://github.com/login/oauth/authorize',
            'token_url': 'https://github.com/login/oauth/access_token',
            'userinfo_url': 'https://api.github.com/user',
            'scope': 'user:email',
            'client_id': settings.GITHUB_CLIENT_ID,
            'client_secret': settings.GITHUB_CLIENT_SECRET,
            'redirect_uri': settings.GITHUB_REDIRECT_URI or 'http://localhost:8000/api/v1/auth/oauth/github/callback'
        }
    }
    
    @staticmethod
    def get_authorization_url(provider: str, state: Optional[str] = None) -> str:
        """
        Generate OAuth authorization URL for the specified provider
        
        Args:
            provider: OAuth provider name (google, github, etc.)
            state: CSRF protection state parameter
            
        Returns:
            Authorization URL string
            
        Raises:
            HTTPException: If provider is not supported or not configured
        """
        if provider not in OAuthService.PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}"
            )
        
        config = OAuthService.PROVIDERS[provider]
        
        if not config['client_id'] or not config['client_secret']:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"OAuth provider {provider} is not configured"
            )
        
        # Generate state for CSRF protection if not provided
        if not state:
            state = str(uuid.uuid4())
        
        params = {
            'client_id': config['client_id'],
            'redirect_uri': config['redirect_uri'],
            'scope': config['scope'],
            'response_type': 'code',
            'state': state,
            'access_type': 'offline',  # For refresh tokens (Google)
            'prompt': 'consent'  # Force consent screen (Google)
        }
        
        auth_url = f"{config['auth_url']}?{urlencode(params)}"
        logger.info(f"Generated {provider} OAuth URL with state: {state}")
        
        return auth_url
    
    @staticmethod
    async def exchange_code_for_token(provider: str, code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            provider: OAuth provider name
            code: Authorization code from OAuth callback
            state: CSRF protection state parameter
            
        Returns:
            Token response dictionary
            
        Raises:
            HTTPException: If token exchange fails
        """
        if provider not in OAuthService.PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}"
            )
        
        config = OAuthService.PROVIDERS[provider]
        
        token_data = {
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': config['redirect_uri']
        }
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config['token_url'],
                    data=token_data,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Token exchange failed for {provider}: {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to exchange code for token"
                    )
                
                token_response = response.json()
                logger.info(f"Successfully exchanged code for {provider} token")
                
                return token_response
                
        except httpx.TimeoutException:
            logger.error(f"Timeout during token exchange for {provider}")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="OAuth token exchange timed out"
            )
        except Exception as e:
            logger.error(f"Error during token exchange for {provider}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OAuth token exchange failed"
            )
    
    @staticmethod
    async def get_user_info(provider: str, access_token: str) -> Dict[str, Any]:
        """
        Get user information from OAuth provider
        
        Args:
            provider: OAuth provider name
            access_token: OAuth access token
            
        Returns:
            User information dictionary
            
        Raises:
            HTTPException: If user info retrieval fails
        """
        if provider not in OAuthService.PROVIDERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}"
            )
        
        config = OAuthService.PROVIDERS[provider]
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    config['userinfo_url'],
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to get user info from {provider}: {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to retrieve user information"
                    )
                
                user_info = response.json()
                
                # Handle GitHub private emails
                if provider == 'github' and not user_info.get('email'):
                    github_emails = await OAuthService._get_github_emails(access_token)
                    # Find primary email or first verified email
                    primary_email = next((e for e in github_emails if e.get('primary')), None)
                    if not primary_email:
                        primary_email = next((e for e in github_emails if e.get('verified')), None)
                    if primary_email:
                        user_info['email'] = primary_email.get('email')
                
                # Normalize user info format across providers
                normalized_info = OAuthService._normalize_user_info(provider, user_info)
                
                logger.info(f"Successfully retrieved user info from {provider} for user: {normalized_info.get('email', 'unknown')}")
                
                return normalized_info
                
        except httpx.TimeoutException:
            logger.error(f"Timeout during user info retrieval from {provider}")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="User info retrieval timed out"
            )
        except Exception as e:
            logger.error(f"Error getting user info from {provider}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user information"
            )
    
    @staticmethod
    async def _get_github_emails(access_token: str) -> list:
        """
        Get GitHub user emails (needed for private emails)
        
        Args:
            access_token: GitHub OAuth access token
            
        Returns:
            List of GitHub email objects
        """
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get('https://api.github.com/user/emails', headers=headers)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to fetch GitHub emails: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching GitHub emails: {str(e)}")
            return []

    @staticmethod
    def _normalize_user_info(provider: str, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize user information format across different providers
        
        Args:
            provider: OAuth provider name
            user_info: Raw user info from provider
            
        Returns:
            Normalized user info dictionary
        """
        if provider == 'google':
            return {
                'provider_id': user_info.get('id'),
                'email': user_info.get('email'),
                'email_verified': user_info.get('verified_email', False),
                'first_name': user_info.get('given_name'),
                'last_name': user_info.get('family_name'),
                'display_name': user_info.get('name'),
                'profile_picture_url': user_info.get('picture'),
                'locale': user_info.get('locale'),
                'raw_data': user_info
            }
        elif provider == 'github':
            return {
                'provider_id': str(user_info.get('id')),
                'email': user_info.get('email'),
                'email_verified': True,  # GitHub emails are verified
                'first_name': None,  # GitHub doesn't provide split names
                'last_name': None,
                'display_name': user_info.get('name') or user_info.get('login'),
                'username': user_info.get('login'),
                'profile_picture_url': user_info.get('avatar_url'),
                'bio': user_info.get('bio'),
                'raw_data': user_info
            }
        
        # Default format
        return {
            'provider_id': str(user_info.get('id')),
            'email': user_info.get('email'),
            'email_verified': False,
            'display_name': user_info.get('name'),
            'profile_picture_url': user_info.get('avatar_url') or user_info.get('picture'),
            'raw_data': user_info
        }
    
    @staticmethod
    async def create_or_update_user(provider: str, user_info: Dict[str, Any], token_info: Dict[str, Any]) -> Tuple[User, bool]:
        """
        Create new user or update existing user with OAuth information
        
        Args:
            provider: OAuth provider name
            user_info: Normalized user information
            token_info: OAuth token information
            
        Returns:
            Tuple of (User object, is_new_user boolean)
            
        Raises:
            HTTPException: If user creation/update fails
        """
        session = await get_db_session()
        
        try:
            email = user_info.get('email')
            provider_id = user_info.get('provider_id')
            
            if not email or not provider_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email and provider ID are required"
                )
            
            # Check if social account already exists
            social_result = await session.execute(
                select(SocialAccount).where(
                    SocialAccount.provider == provider,
                    SocialAccount.provider_id == provider_id
                )
            )
            social_account = social_result.scalar_one_or_none()
            
            if social_account:
                # Update existing social account
                user = await session.get(User, social_account.user_id)
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Associated user not found"
                    )
                is_new_user = False
                
                # Update social account with new info
                social_account.access_token = token_info.get('access_token')
                social_account.refresh_token = token_info.get('refresh_token')
                social_account.email = email
                social_account.display_name = user_info.get('display_name')
                social_account.first_name = user_info.get('first_name')
                social_account.last_name = user_info.get('last_name')
                social_account.profile_picture_url = user_info.get('profile_picture_url')
                social_account.last_login = datetime.now(timezone.utc)
                social_account.provider_data = json.dumps(user_info.get('raw_data', {}))
                
                # Update token expiration if provided
                if 'expires_in' in token_info:
                    social_account.token_expires_at = datetime.now(timezone.utc).replace(
                        microsecond=0
                    ) + timedelta(seconds=int(token_info['expires_in']))
                
                logger.info(f"Updated existing social account for {provider} user: {email}")
            
            else:
                # Check if user exists with this email
                user_result = await session.execute(
                    select(User).where(User.email == email)
                )
                user = user_result.scalar_one_or_none()
                
                if user:
                    # Link social account to existing user
                    is_new_user = False
                    logger.info(f"Linking {provider} account to existing user: {email}")
                else:
                    # Create new user
                    user = User(
                        email=email,
                        is_verified=user_info.get('email_verified', False),
                        is_active=True,
                        first_name=user_info.get('first_name'),
                        last_name=user_info.get('last_name'),
                        display_name=user_info.get('display_name'),
                        profile_picture_url=user_info.get('profile_picture_url')
                    )
                    session.add(user)
                    await session.flush()  # Get user ID
                    is_new_user = True
                    logger.info(f"Created new user from {provider}: {email}")
                
                # Create social account
                social_account = SocialAccount(
                    user_id=user.id,
                    provider=provider,
                    provider_id=provider_id,
                    email=email,
                    username=user_info.get('username'),
                    display_name=user_info.get('display_name'),
                    first_name=user_info.get('first_name'),
                    last_name=user_info.get('last_name'),
                    profile_picture_url=user_info.get('profile_picture_url'),
                    access_token=token_info.get('access_token'),
                    refresh_token=token_info.get('refresh_token'),
                    is_verified=user_info.get('email_verified', False),
                    is_primary=True,  # First social account is primary
                    scope=token_info.get('scope'),
                    provider_data=json.dumps(user_info.get('raw_data', {})),
                    last_login=datetime.now(timezone.utc)
                )
                
                # Set token expiration if provided
                if 'expires_in' in token_info:
                    social_account.token_expires_at = datetime.now(timezone.utc).replace(
                        microsecond=0
                    ) + timedelta(seconds=int(token_info['expires_in']))
                
                session.add(social_account)
            
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"Successfully processed OAuth user: {email} (new: {is_new_user})")
            return user, is_new_user
            
        except IntegrityError as e:
            await session.rollback()
            logger.error(f"Database integrity error during OAuth user creation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User account conflict"
            )
        except Exception as e:
            await session.rollback()
            logger.error(f"Error creating/updating OAuth user: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create or update user account"
            )
        finally:
            await session.close()
    
    @staticmethod
    async def authenticate_oauth_user(provider: str, code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete OAuth authentication flow
        
        Args:
            provider: OAuth provider name
            code: Authorization code from OAuth callback
            state: CSRF protection state parameter
            
        Returns:
            Authentication response with user and tokens
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            # Exchange code for token
            token_info = await OAuthService.exchange_code_for_token(provider, code, state)
            
            # Get user information
            user_info = await OAuthService.get_user_info(provider, token_info['access_token'])
            
            # Create or update user
            user, is_new_user = await OAuthService.create_or_update_user(provider, user_info, token_info)
            
            # Generate JWT tokens
            access_token = create_access_token(subject=str(user.id))
            refresh_token = create_refresh_token(subject=str(user.id))
            
            logger.info(f"OAuth authentication successful for {provider} user: {user.email}")
            
            return {
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "display_name": user.display_name,
                    "profile_picture_url": user.profile_picture_url,
                    "is_verified": user.is_verified,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None
                },
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer"
                },
                "is_new_user": is_new_user,
                "provider": provider
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"OAuth authentication failed for {provider}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OAuth authentication failed"
            )


# Import datetime, timedelta at the top
from datetime import timedelta
