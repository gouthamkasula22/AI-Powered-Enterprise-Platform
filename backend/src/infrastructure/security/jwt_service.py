"""
Security Infrastructure

Provides JWT token generation, validation, and security utilities
for authentication and authorization.
"""

import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    """Types of JWT tokens"""
    ACCESS = "access"
    REFRESH = "refresh"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"


@dataclass
class TokenData:
    """Token payload data"""
    user_id: int
    email: str
    token_type: TokenType
    expires_at: datetime
    issued_at: datetime
    role: Optional[str] = None  # User's role for RBAC
    jti: Optional[str] = None  # JWT ID for blacklisting
    scopes: Optional[List[str]] = None
    permissions: Optional[List[str]] = None  # User's permissions


class JWTService:
    """
    JWT token service for authentication.
    
    Handles token creation, validation, and security features
    like token blacklisting and refresh rotation.
    """
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
    
    def create_access_token(
        self, 
        user_id: int, 
        email: str,
        role: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None
    ) -> str:
        """Create a new access token with role and permissions"""
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "user_id": user_id,
            "email": email,
            "role": role,
            "token_type": TokenType.ACCESS.value,
            "exp": expires_at,
            "iat": now,
            "jti": secrets.token_urlsafe(32),
            "scopes": scopes or [],
            "permissions": permissions or []
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: int, email: str) -> str:
        """Create a new refresh token"""
        now = datetime.utcnow()
        expires_at = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "user_id": user_id,
            "email": email,
            "token_type": TokenType.REFRESH.value,
            "exp": expires_at,
            "iat": now,
            "jti": secrets.token_urlsafe(32)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_verification_token(self, user_id: int, email: str) -> str:
        """Create email verification token"""
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=24)  # 24 hour expiration
        
        payload = {
            "user_id": user_id,
            "email": email,
            "token_type": TokenType.EMAIL_VERIFICATION.value,
            "exp": expires_at,
            "iat": now,
            "jti": secrets.token_urlsafe(32)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_password_reset_token(self, user_id: int, email: str) -> str:
        """Create password reset token"""
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=1)  # 1 hour expiration
        
        payload = {
            "user_id": user_id,
            "email": email,
            "token_type": TokenType.PASSWORD_RESET.value,
            "exp": expires_at,
            "iat": now,
            "jti": secrets.token_urlsafe(32)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def decode_token(self, token: str) -> Optional[TokenData]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            return TokenData(
                user_id=payload["user_id"],
                email=payload["email"],
                token_type=TokenType(payload["token_type"]),
                expires_at=datetime.fromtimestamp(payload["exp"]),
                issued_at=datetime.fromtimestamp(payload["iat"]),
                role=payload.get("role"),
                jti=payload.get("jti"),
                scopes=payload.get("scopes"),
                permissions=payload.get("permissions")
            )
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None
    
    def get_token_jti(self, token: str) -> Optional[str]:
        """Extract JTI from token without full validation"""
        try:
            # Decode without verification to get JTI for blacklisting
            payload = jwt.decode(
                token, 
                options={"verify_signature": False, "verify_exp": False}
            )
            return payload.get("jti")
        except Exception:
            return None


class TokenBlacklistService:
    """
    Token blacklisting service using cache.
    
    Maintains a blacklist of invalidated JWT tokens to prevent reuse
    of compromised or logged-out tokens.
    """
    
    def __init__(self, cache_service):
        from ..cache import CacheService
        self.cache: CacheService = cache_service
        self.blacklist_prefix = "blacklist:"
    
    async def blacklist_token(self, jti: str, expires_at: datetime) -> bool:
        """Add token to blacklist"""
        if not jti:
            return False
        
        key = f"{self.blacklist_prefix}{jti}"
        # Set expiration to match token expiration
        expire_delta = expires_at - datetime.utcnow()
        
        if expire_delta.total_seconds() > 0:
            return await self.cache.set(key, True, expire_delta)
        
        return True  # Already expired
    
    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        if not jti:
            return False
        
        key = f"{self.blacklist_prefix}{jti}"
        return await self.cache.exists(key)
    
    async def blacklist_all_user_tokens(self, user_id: int) -> bool:
        """
        Blacklist all tokens for a user.
        
        This is done by setting a timestamp after which all tokens
        for the user are considered invalid.
        """
        key = f"user_token_invalidate:{user_id}"
        invalidate_time = datetime.utcnow()
        
        # Store indefinitely - we'll check token issue time against this
        return await self.cache.set(key, invalidate_time.isoformat())
    
    async def get_user_token_invalidate_time(self, user_id: int) -> Optional[datetime]:
        """Get the time after which all user tokens are invalid"""
        key = f"user_token_invalidate:{user_id}"
        timestamp_str = await self.cache.get(key)
        
        if timestamp_str:
            try:
                return datetime.fromisoformat(timestamp_str)
            except ValueError:
                return None
        
        return None


class SecurityUtils:
    """General security utilities"""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_verification_code(length: int = 6) -> str:
        """Generate a numeric verification code"""
        return ''.join(secrets.choice('0123456789') for _ in range(length))
    
    @staticmethod
    def constant_time_compare(a: str, b: str) -> bool:
        """Constant-time string comparison to prevent timing attacks"""
        return secrets.compare_digest(a, b)


class AuthenticationService:
    """
    High-level authentication service.
    
    Combines JWT service with blacklisting for complete auth functionality.
    """
    
    def __init__(self, jwt_service: JWTService, blacklist_service: TokenBlacklistService):
        self.jwt_service = jwt_service
        self.blacklist_service = blacklist_service
    
    async def create_token_pair(
        self, 
        user_id: int, 
        email: str, 
        role: Optional[str] = None, 
        permissions: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """Create access and refresh token pair with role information"""
        access_token = self.jwt_service.create_access_token(
            user_id, email, role=role, permissions=permissions
        )
        refresh_token = self.jwt_service.create_refresh_token(user_id, email)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    async def validate_token(self, token: str, expected_type: TokenType) -> Optional[TokenData]:
        """Validate token and check blacklist"""
        token_data = self.jwt_service.decode_token(token)
        
        if not token_data or token_data.token_type != expected_type:
            return None
        
        # Check if token is blacklisted
        if token_data.jti and await self.blacklist_service.is_token_blacklisted(token_data.jti):
            return None
        
        # Check if all user tokens are invalidated
        invalidate_time = await self.blacklist_service.get_user_token_invalidate_time(
            token_data.user_id
        )
        if invalidate_time and token_data.issued_at < invalidate_time:
            return None
        
        return token_data
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh access token using refresh token"""
        token_data = await self.validate_token(refresh_token, TokenType.REFRESH)
        
        if not token_data:
            return None
        
        # Blacklist old refresh token
        if token_data.jti:
            await self.blacklist_service.blacklist_token(
                token_data.jti, 
                token_data.expires_at
            )
        
        # Create new token pair
        return await self.create_token_pair(token_data.user_id, token_data.email)
    
    async def logout_token(self, token: str) -> bool:
        """Logout by blacklisting token"""
        jti = self.jwt_service.get_token_jti(token)
        if jti:
            token_data = self.jwt_service.decode_token(token)
            if token_data:
                return await self.blacklist_service.blacklist_token(
                    jti, 
                    token_data.expires_at
                )
        
        return False
    
    async def logout_all_user_tokens(self, user_id: int) -> bool:
        """Logout all tokens for a user"""
        return await self.blacklist_service.blacklist_all_user_tokens(user_id)


# Global security services
_jwt_service: Optional[JWTService] = None
_blacklist_service: Optional[TokenBlacklistService] = None
_auth_service: Optional[AuthenticationService] = None


def configure_security(
    secret_key: str,
    cache_service,
    algorithm: str = "HS256",
    access_token_expire_minutes: int = 30,
    refresh_token_expire_days: int = 7
) -> AuthenticationService:
    """Configure security services"""
    global _jwt_service, _blacklist_service, _auth_service
    
    _jwt_service = JWTService(
        secret_key=secret_key,
        algorithm=algorithm,
        access_token_expire_minutes=access_token_expire_minutes,
        refresh_token_expire_days=refresh_token_expire_days
    )
    
    _blacklist_service = TokenBlacklistService(cache_service)
    _auth_service = AuthenticationService(_jwt_service, _blacklist_service)
    
    return _auth_service


def get_jwt_service() -> JWTService:
    """Get JWT service instance"""
    if _jwt_service is None:
        raise RuntimeError("Security not configured. Call configure_security() first.")
    return _jwt_service


def get_blacklist_service() -> TokenBlacklistService:
    """Get blacklist service instance"""
    if _blacklist_service is None:
        raise RuntimeError("Security not configured. Call configure_security() first.")
    return _blacklist_service


def get_auth_service() -> AuthenticationService:
    """Get authentication service instance"""
    if _auth_service is None:
        raise RuntimeError("Security not configured. Call configure_security() first.")
    return _auth_service