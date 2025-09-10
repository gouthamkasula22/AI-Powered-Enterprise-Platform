"""
Security utilities for password hashing, JWT tokens, and authentication.
Enhanced for M1.3 Authentication Services implementation.
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional, Dict
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings

# Password hashing context using Argon2 (modern and secure)
pwd_context = CryptContext(
    schemes=["argon2"], 
    deprecated="auto",
    argon2__rounds=4,
    argon2__memory_cost=102400,  # 100MB in KB
    argon2__parallelism=8
)


class SecurityConfig:
    """Security configuration constants"""
    
    # Password Configuration
    MIN_PASSWORD_LENGTH: int = 8
    MAX_PASSWORD_LENGTH: int = 128
    
    # Rate Limiting
    LOGIN_ATTEMPT_LIMIT: int = 5
    LOGIN_ATTEMPT_WINDOW_MINUTES: int = 15


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength requirements
    
    Args:
        password: Password to validate
        
    Returns:
        Dictionary with validation results
    """
    validation = {
        "valid": True,
        "errors": [],
        "strength_score": 0,
        "requirements": {
            "length": False,
            "uppercase": False,
            "lowercase": False,
            "digit": False,
            "special": False
        }
    }
    
    # Length check
    if len(password) >= SecurityConfig.MIN_PASSWORD_LENGTH:
        validation["requirements"]["length"] = True
        validation["strength_score"] += 20
    else:
        validation["errors"].append(f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters long")
        validation["valid"] = False
        
    if len(password) > SecurityConfig.MAX_PASSWORD_LENGTH:
        validation["errors"].append(f"Password must be no more than {SecurityConfig.MAX_PASSWORD_LENGTH} characters long")
        validation["valid"] = False
    
    # Character type checks
    if any(c.isupper() for c in password):
        validation["requirements"]["uppercase"] = True
        validation["strength_score"] += 20
    else:
        validation["errors"].append("Password must contain at least one uppercase letter")
        validation["valid"] = False
        
    if any(c.islower() for c in password):
        validation["requirements"]["lowercase"] = True
        validation["strength_score"] += 20
    else:
        validation["errors"].append("Password must contain at least one lowercase letter")
        validation["valid"] = False
        
    if any(c.isdigit() for c in password):
        validation["requirements"]["digit"] = True
        validation["strength_score"] += 20
    else:
        validation["errors"].append("Password must contain at least one digit")
        validation["valid"] = False
        
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        validation["requirements"]["special"] = True
        validation["strength_score"] += 20
    else:
        validation["errors"].append("Password must contain at least one special character")
        validation["valid"] = False
    
    return validation

def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Verify and decode a JWT token, return user_id if valid"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str | None = payload.get("sub")
        return user_id if user_id is not None else None
    except JWTError:
        return None


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token with exception handling
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def generate_random_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token
    
    Args:
        length: Length of the token
        
    Returns:
        Random token string
    """
    return secrets.token_urlsafe(length)


def generate_device_fingerprint(user_agent: str, ip_address: str) -> str:
    """
    Generate a device fingerprint for session tracking
    
    Args:
        user_agent: User agent string
        ip_address: Client IP address
        
    Returns:
        Device fingerprint hash
    """
    import hashlib
    fingerprint_data = f"{user_agent}:{ip_address}:{secrets.token_hex(8)}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()
