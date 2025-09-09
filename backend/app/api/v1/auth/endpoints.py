"""
Authentication API Endpoints

FastAPI endpoints for user authentication including registration, login,
logout, token refresh, and password management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    PasswordChangeRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    RefreshTokenRequest,
    AuthResponse,
    TokenResponse,
    UserInfoResponse,
    LogoutResponse,
    SuccessResponse,
    PasswordValidationResponse
)
from app.services.auth_service import AuthenticationService
from app.core.security import validate_password_strength, verify_token

# Create router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security scheme for JWT tokens
security = HTTPBearer()


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded IP first (for reverse proxies)
    forwarded_ip = request.headers.get("X-Forwarded-For")
    if forwarded_ip:
        return forwarded_ip.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("User-Agent", "unknown")


async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency to extract and validate current user from JWT token
    
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


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: UserRegisterRequest
) -> AuthResponse:
    """
    Register a new user account
    
    Creates a new user with email and password, returns JWT tokens for immediate login.
    
    Args:
        request: FastAPI request object
        user_data: User registration data
        
    Returns:
        User information and JWT tokens
        
    Raises:
        HTTPException: If registration fails
    """
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    result = await AuthenticationService.register_user(
        email=user_data.email,
        password=user_data.password,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return AuthResponse(**result)


@router.post("/login", response_model=AuthResponse)
async def login(
    request: Request,
    login_data: UserLoginRequest
) -> AuthResponse:
    """
    Authenticate user and create session
    
    Validates user credentials and returns JWT tokens for authenticated access.
    
    Args:
        request: FastAPI request object
        login_data: User login credentials
        
    Returns:
        User information and JWT tokens
        
    Raises:
        HTTPException: If authentication fails
    """
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    result = await AuthenticationService.authenticate_user(
        email=login_data.email,
        password=login_data.password,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return AuthResponse(**result)


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    current_user_id: str = Depends(get_current_user_id)
) -> LogoutResponse:
    """
    Logout current user and invalidate session
    
    Args:
        current_user_id: Current authenticated user ID
        
    Returns:
        Logout confirmation
    """
    # TODO: Implement session invalidation in AuthenticationService
    # For now, return success (client should discard tokens)
    return LogoutResponse(message="Logged out successfully")


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user(
    current_user_id: str = Depends(get_current_user_id)
) -> UserInfoResponse:
    """
    Get current user information
    
    Args:
        current_user_id: Current authenticated user ID
        
    Returns:
        Current user information
    """
    # TODO: Implement user retrieval in AuthenticationService
    # For now, return placeholder
    from app.schemas.auth import UserResponse
    from datetime import datetime
    
    user = UserResponse(
        id=current_user_id,
        email="user@example.com",  # TODO: Get from database
        created_at=datetime.utcnow()
    )
    
    return UserInfoResponse(user=user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest
) -> TokenResponse:
    """
    Refresh JWT access token
    
    Args:
        refresh_data: Refresh token data
        
    Returns:
        New JWT tokens
    """
    # TODO: Implement token refresh in AuthenticationService
    # For now, return placeholder
    from app.core.security import create_access_token, create_refresh_token
    
    # Verify refresh token and extract user ID
    user_id = verify_token(refresh_data.refresh_token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new tokens
    new_access_token = create_access_token(subject=user_id)
    new_refresh_token = create_refresh_token(subject=user_id)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )


@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user_id: str = Depends(get_current_user_id)
) -> SuccessResponse:
    """
    Change user password
    
    Args:
        password_data: Current and new password data
        current_user_id: Current authenticated user ID
        
    Returns:
        Success confirmation
    """
    # TODO: Implement password change in AuthenticationService
    return SuccessResponse(message="Password changed successfully", data=None)


@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(
    forgot_data: ForgotPasswordRequest
) -> SuccessResponse:
    """
    Request password reset
    
    Args:
        forgot_data: Email for password reset
        
    Returns:
        Success confirmation
    """
    # TODO: Implement password reset initiation
    return SuccessResponse(message="Password reset email sent if account exists", data=None)


@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(
    reset_data: ResetPasswordRequest
) -> SuccessResponse:
    """
    Reset password with token
    
    Args:
        reset_data: Reset token and new password
        
    Returns:
        Success confirmation
    """
    # TODO: Implement password reset completion
    return SuccessResponse(message="Password reset successfully", data=None)


@router.post("/validate-password", response_model=PasswordValidationResponse)
async def validate_password(
    password: str
) -> PasswordValidationResponse:
    """
    Validate password strength
    
    Args:
        password: Password to validate
        
    Returns:
        Password validation results
    """
    validation = validate_password_strength(password)
    return PasswordValidationResponse(**validation)
