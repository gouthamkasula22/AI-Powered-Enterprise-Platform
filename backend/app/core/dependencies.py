"""
Dependency Injection

Common dependencies for FastAPI endpoints
"""

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import verify_token
from app.core.database import get_db_session
from app.models import User

logger = logging.getLogger(__name__)

# Security scheme for JWT tokens
security = HTTPBearer()


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency to extract and validate current user ID from JWT token
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        User ID from valid token
        
    Raises:
        HTTPException: If token is invalid
    """
    user_id = verify_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


async def get_current_user(
    current_user_id: str = Depends(get_current_user_id)
) -> User:
    """
    Dependency to get current user object from database
    
    Args:
        current_user_id: User ID from JWT token
        
    Returns:
        User object from database
        
    Raises:
        HTTPException: If user not found or inactive
    """
    session = await get_db_session()
    
    try:
        user = await session.get(User, current_user_id)
        
        if not user:
            logger.warning(f"User not found for ID: {current_user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        return user
        
    finally:
        await session.close()
