"""
OAuth Authentication Endpoints

Handles OAuth 2.0 authentication flows for third-party providers
"""

import logging
from typing import Dict, Any, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse

from app.services.oauth_service import OAuthService
from app.core.dependencies import get_current_user
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth", tags=["OAuth Authentication"])


@router.get("/providers")
async def get_oauth_providers() -> Dict[str, Any]:
    """
    Get list of available OAuth providers
    
    Returns:
        List of configured OAuth providers
    """
    providers = []
    
    for provider_name, config in OAuthService.PROVIDERS.items():
        if config['client_id'] and config['client_secret']:
            providers.append({
                "name": provider_name,
                "display_name": provider_name.title(),
                "login_url": f"/api/v1/auth/oauth/{provider_name}/login"
            })
    
    return {
        "providers": providers,
        "count": len(providers)
    }


@router.get("/{provider}/login")
async def oauth_login(
    provider: str,
    request: Request,
    redirect_uri: Optional[str] = Query(None, description="Custom redirect URI after auth")
) -> RedirectResponse:
    """
    Initiate OAuth login flow
    
    Args:
        provider: OAuth provider name (google, github, etc.)
        redirect_uri: Optional custom redirect URI
        
    Returns:
        Redirect to OAuth provider authorization URL
    """
    try:
        # Generate state for CSRF protection
        import uuid
        state = str(uuid.uuid4())
        
        # Store state and redirect_uri in session or cache
        # For now, we'll encode redirect_uri in state (in production, use secure session storage)
        if redirect_uri:
            state_data = f"{state}|{redirect_uri}"
        else:
            state_data = state
        
        # Get authorization URL
        auth_url = OAuthService.get_authorization_url(provider, state_data)
        
        logger.info(f"Initiating OAuth login for {provider} with state: {state}")
        
        return RedirectResponse(url=auth_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating OAuth login for {provider}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate OAuth login"
        )


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str = Query(..., description="Authorization code from OAuth provider"),
    state: Optional[str] = Query(None, description="CSRF protection state parameter"),
    error: Optional[str] = Query(None, description="Error from OAuth provider"),
    error_description: Optional[str] = Query(None, description="Error description from OAuth provider")
) -> RedirectResponse:
    """
    Handle OAuth callback and complete authentication
    
    Args:
        provider: OAuth provider name
        code: Authorization code from provider
        state: CSRF protection state
        error: Error code if auth failed
        error_description: Error description if auth failed
        
    Returns:
        Redirect to frontend with auth result
    """
    try:
        # Check for OAuth provider errors
        if error:
            logger.warning(f"OAuth error from {provider}: {error} - {error_description}")
            error_params = urlencode({
                "error": error,
                "error_description": error_description or "OAuth authentication failed"
            })
            return RedirectResponse(
                url=f"http://localhost:3000/auth/callback?{error_params}"
            )
        
        if not code:
            logger.error(f"No authorization code received from {provider}")
            error_params = urlencode({
                "error": "missing_code",
                "error_description": "No authorization code received"
            })
            return RedirectResponse(
                url=f"http://localhost:3000/auth/callback?{error_params}"
            )
        
        # Parse state to extract redirect URI if present
        redirect_uri = "http://localhost:3000/dashboard"  # Default
        if state and "|" in state:
            state_parts = state.split("|", 1)
            state = state_parts[0]
            redirect_uri = state_parts[1]
        
        # Complete OAuth authentication
        auth_result = await OAuthService.authenticate_oauth_user(provider, code, state)
        
        # Create success response with tokens
        success_params = urlencode({
            "success": "true",
            "access_token": auth_result["tokens"]["access_token"],
            "refresh_token": auth_result["tokens"]["refresh_token"],
            "user_id": auth_result["user"]["id"],
            "email": auth_result["user"]["email"],
            "display_name": auth_result["user"]["display_name"] or "",
            "is_new_user": str(auth_result["is_new_user"]).lower(),
            "provider": provider
        })
        
        # Redirect to specified URI or default dashboard
        final_redirect = f"{redirect_uri}?{success_params}"
        
        logger.info(f"OAuth callback successful for {provider}, redirecting to: {redirect_uri}")
        
        return RedirectResponse(url=final_redirect)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OAuth callback for {provider}: {str(e)}")
        error_params = urlencode({
            "error": "callback_error",
            "error_description": "OAuth callback processing failed"
        })
        return RedirectResponse(
            url=f"http://localhost:3000/auth/callback?{error_params}"
        )


@router.post("/{provider}/link")
async def link_oauth_account(
    provider: str,
    code: str,
    state: Optional[str] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Link OAuth account to existing authenticated user
    
    Args:
        provider: OAuth provider name
        code: Authorization code from provider
        state: CSRF protection state
        current_user: Currently authenticated user
        
    Returns:
        Updated user information with linked account
    """
    try:
        # Exchange code for token
        token_info = await OAuthService.exchange_code_for_token(provider, code, state)
        
        # Get user information from provider
        user_info = await OAuthService.get_user_info(provider, token_info['access_token'])
        
        # Check if this OAuth account is already linked to another user
        from app.core.database import get_db_session
        from sqlalchemy import select
        from app.models import SocialAccount
        
        session = await get_db_session()
        
        try:
            existing_account = await session.execute(
                select(SocialAccount).where(
                    SocialAccount.provider == provider,
                    SocialAccount.provider_id == user_info.get('provider_id')
                )
            )
            existing = existing_account.scalar_one_or_none()
            
            if existing and existing.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"This {provider} account is already linked to another user"
                )
            
            # Create or update social account for current user
            if existing:
                # Update existing link
                existing.access_token = token_info.get('access_token')
                existing.refresh_token = token_info.get('refresh_token')
                existing.email = user_info.get('email')
                existing.display_name = user_info.get('display_name')
                existing.first_name = user_info.get('first_name')
                existing.last_name = user_info.get('last_name')
                existing.profile_picture_url = user_info.get('profile_picture_url')
                
                if 'expires_in' in token_info:
                    from datetime import datetime, timezone, timedelta
                    existing.token_expires_at = datetime.now(timezone.utc).replace(
                        microsecond=0
                    ) + timedelta(seconds=int(token_info['expires_in']))
                
                await session.commit()
                
                logger.info(f"Updated {provider} account link for user: {current_user.email}")
                
            else:
                # Create new link
                import json
                from datetime import datetime, timezone, timedelta
                
                social_account = SocialAccount(
                    user_id=current_user.id,
                    provider=provider,
                    provider_id=user_info.get('provider_id'),
                    email=user_info.get('email'),
                    username=user_info.get('username'),
                    display_name=user_info.get('display_name'),
                    first_name=user_info.get('first_name'),
                    last_name=user_info.get('last_name'),
                    profile_picture_url=user_info.get('profile_picture_url'),
                    access_token=token_info.get('access_token'),
                    refresh_token=token_info.get('refresh_token'),
                    is_verified=user_info.get('email_verified', False),
                    is_primary=False,  # Additional accounts are not primary
                    scope=token_info.get('scope'),
                    provider_data=json.dumps(user_info.get('raw_data', {})),
                    last_login=datetime.now(timezone.utc)
                )
                
                if 'expires_in' in token_info:
                    social_account.token_expires_at = datetime.now(timezone.utc).replace(
                        microsecond=0
                    ) + timedelta(seconds=int(token_info['expires_in']))
                
                session.add(social_account)
                await session.commit()
                
                logger.info(f"Linked new {provider} account to user: {current_user.email}")
            
            # Get updated user with linked accounts
            linked_accounts = await session.execute(
                select(SocialAccount).where(SocialAccount.user_id == current_user.id)
            )
            accounts = linked_accounts.scalars().all()
            
            return {
                "message": f"Successfully linked {provider} account",
                "user": {
                    "id": str(current_user.id),
                    "email": current_user.email,
                    "display_name": current_user.display_name,
                    "linked_accounts": [
                        {
                            "provider": account.provider,
                            "provider_id": account.provider_id,
                            "email": account.email,
                            "display_name": account.display_name,
                            "is_primary": account.is_primary,
                            "linked_at": account.created_at.isoformat() if account.created_at else None
                        }
                        for account in accounts
                    ]
                }
            }
            
        finally:
            await session.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking {provider} account for user {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link {provider} account"
        )


@router.delete("/{provider}/unlink")
async def unlink_oauth_account(
    provider: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Unlink OAuth account from current user
    
    Args:
        provider: OAuth provider name
        current_user: Currently authenticated user
        
    Returns:
        Success message
    """
    try:
        from app.core.database import get_db_session
        from sqlalchemy import select, delete
        from app.models import SocialAccount
        
        session = await get_db_session()
        
        try:
            # Find the social account to unlink
            result = await session.execute(
                select(SocialAccount).where(
                    SocialAccount.user_id == current_user.id,
                    SocialAccount.provider == provider
                )
            )
            social_account = result.scalar_one_or_none()
            
            if not social_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No {provider} account linked to this user"
                )
            
            # Check if this is the only authentication method
            all_accounts = await session.execute(
                select(SocialAccount).where(SocialAccount.user_id == current_user.id)
            )
            account_count = len(all_accounts.scalars().all())
            
            # If user has no password and this is their only social account, prevent unlinking
            if not current_user.password_hash and account_count == 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot unlink the only authentication method. Set a password first."
                )
            
            # Delete the social account
            await session.execute(
                delete(SocialAccount).where(
                    SocialAccount.user_id == current_user.id,
                    SocialAccount.provider == provider
                )
            )
            await session.commit()
            
            logger.info(f"Unlinked {provider} account from user: {current_user.email}")
            
            return {
                "message": f"Successfully unlinked {provider} account",
                "provider": provider
            }
            
        finally:
            await session.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unlinking {provider} account for user {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unlink {provider} account"
        )


@router.get("/accounts")
async def get_linked_accounts(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get all OAuth accounts linked to current user
    
    Args:
        current_user: Currently authenticated user
        
    Returns:
        List of linked OAuth accounts
    """
    try:
        from app.core.database import get_db_session
        from sqlalchemy import select
        from app.models import SocialAccount
        
        session = await get_db_session()
        
        try:
            result = await session.execute(
                select(SocialAccount).where(SocialAccount.user_id == current_user.id)
            )
            accounts = result.scalars().all()
            
            linked_accounts = [
                {
                    "provider": account.provider,
                    "provider_id": account.provider_id,
                    "email": account.email,
                    "display_name": account.display_name,
                    "profile_picture_url": account.profile_picture_url,
                    "is_primary": account.is_primary,
                    "is_verified": account.is_verified,
                    "linked_at": account.created_at.isoformat() if account.created_at else None,
                    "last_login": account.last_login.isoformat() if account.last_login else None
                }
                for account in accounts
            ]
            
            return {
                "linked_accounts": linked_accounts,
                "count": len(linked_accounts),
                "has_password": bool(current_user.password_hash)
            }
            
        finally:
            await session.close()
            
    except Exception as e:
        logger.error(f"Error getting linked accounts for user {current_user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve linked accounts"
        )
