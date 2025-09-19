"""
Simple Google OAuth Service

Minimal implementation for Google OAuth 2.0 authentication.
No complex abstractions - just what we need to get user info from Google.
"""

import httpx
import secrets
from urllib.parse import urlencode
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ...shared.config import get_settings


@dataclass
class GoogleUserInfo:
    """Simple container for Google user information"""
    id: str
    email: str
    name: str
    given_name: str
    family_name: str
    picture: str
    verified_email: bool


class SimpleGoogleOAuth:
    """Simple Google OAuth 2.0 service - no complex abstractions"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client_id = self.settings.google_client_id
        self.client_secret = self.settings.google_client_secret
        
        # Google OAuth URLs
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    def get_authorization_url(self, redirect_uri: str) -> tuple[str, str]:
        """
        Get Google OAuth authorization URL and state
        
        Returns:
            tuple[auth_url, state] - The authorization URL and state for CSRF protection
        """
        state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        auth_url = f"{self.auth_url}?{urlencode(params)}"
        return auth_url, state
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> str:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from Google
            redirect_uri: Same redirect URI used in authorization
            
        Returns:
            access_token: Google access token
        """
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            return token_data["access_token"]
    
    async def get_user_info(self, access_token: str) -> GoogleUserInfo:
        """
        Get user information from Google using access token
        
        Args:
            access_token: Google access token
            
        Returns:
            GoogleUserInfo: User information from Google
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.userinfo_url, headers=headers)
            response.raise_for_status()
            
            user_data = response.json()
            
            return GoogleUserInfo(
                id=user_data["id"],
                email=user_data["email"],
                name=user_data.get("name", ""),
                given_name=user_data.get("given_name", ""),
                family_name=user_data.get("family_name", ""),
                picture=user_data.get("picture", ""),
                verified_email=user_data.get("verified_email", False)
            )