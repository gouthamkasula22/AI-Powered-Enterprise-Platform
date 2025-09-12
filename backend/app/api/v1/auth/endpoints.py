"""
Authentication API Endpoints

FastAPI endpoints for user authentication including registration, login,
logout, token refresh, and password management.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    PasswordChangeRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    RefreshTokenRequest,
    EmailVerificationRequest,
    ProfileUpdateRequest,
    EmailValidationRequest,
    EmailValidationResponse,
    PasswordValidationRequest,
    PasswordValidationResponse,
    PasswordRequirementCheck,
    ResendVerificationRequest,
    EmailVerificationResponse,
    MessageResponse,
    ResetPasswordResponse,
    ValidateResetTokenRequest,
    ValidateResetTokenResponse,
    AuthResponse,
    TokenResponse,
    UserInfoResponse,
    UserResponse,
    LogoutResponse,
    SuccessResponse
)
from app.services.auth_service import AuthenticationService
from app.services.email_validation_service import EmailValidationService
from app.services.password_validation_service import PasswordValidationService
from app.core.security import validate_password_strength, verify_token

# Import OAuth router
from app.api.v1.auth.oauth import router as oauth_router

# Create router for authentication endpoints
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Include OAuth router
router.include_router(oauth_router)

# Security scheme for JWT tokens
security = HTTPBearer()

# Setup logger
logger = logging.getLogger(__name__)


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
    # Validate email before proceeding with registration
    validation_service = EmailValidationService()
    email_validation = await validation_service.validate_email_comprehensive(user_data.email)
    
    if not email_validation.is_valid:
        detail = f"Invalid email address: {email_validation.reason}"
        if email_validation.suggestion:
            detail += f" Did you mean {email_validation.suggestion}?"
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
    
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
    import uuid
    from app.schemas.auth import UserResponse
    
    try:
        user_uuid = uuid.UUID(current_user_id)
        user = await AuthenticationService.get_user_by_id(user_uuid)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        try:
            # Manually create UserResponse with proper field conversion
            user_data = {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "display_name": user.display_name,
                "bio": user.bio,
                "phone_number": user.phone_number,
                "date_of_birth": user.date_of_birth,
                "profile_picture_url": user.profile_picture_url,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            }
            user_response = UserResponse(**user_data)
            return UserInfoResponse(user=user_response)
        except Exception as validation_error:
            logger.error(f"UserResponse validation error: {str(validation_error)}")
            logger.error(f"User object: {user}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error formatting user data"
            )
        
    except ValueError as ve:
        logger.error(f"UUID conversion error: {str(ve)} for user_id: {current_user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_user_id: str = Depends(get_current_user_id)
) -> UserResponse:
    """
    Update user profile information
    
    Args:
        profile_data: Profile update data
        current_user_id: Current authenticated user ID
        
    Returns:
        Updated user information
        
    Raises:
        HTTPException: If user not found
    """
    import uuid
    
    try:
        user_uuid = uuid.UUID(current_user_id)
        
        # Update profile with provided data
        profile_dict = profile_data.model_dump(exclude_unset=True)
        if not profile_dict:
            # If no data provided, just return current user
            user = await AuthenticationService.get_user_by_id(user_uuid)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            # Manually create UserResponse with proper field conversion
            return UserResponse(
                id=str(user.id),
                email=user.email,
                is_verified=user.is_verified,
                is_active=user.is_active,
                created_at=user.created_at,
                first_name=user.first_name,
                last_name=user.last_name,
                display_name=user.display_name,
                bio=user.bio,
                phone_number=user.phone_number,
                date_of_birth=user.date_of_birth,
                profile_picture_url=user.profile_picture_url
            )
        
        updated_user = await AuthenticationService.update_user_profile(user_uuid, profile_dict)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Manually create UserResponse with proper field conversion
        return UserResponse(
            id=str(updated_user.id),
            email=updated_user.email,
            is_verified=updated_user.is_verified,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            display_name=updated_user.display_name,
            bio=updated_user.bio,
            phone_number=updated_user.phone_number,
            date_of_birth=updated_user.date_of_birth,
            profile_picture_url=updated_user.profile_picture_url
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


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


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user_id: str = Depends(get_current_user_id)
) -> MessageResponse:
    """
    Change user password
    
    Args:
        password_data: Current and new password data
        current_user_id: Current authenticated user ID
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If password change fails
    """
    import uuid
    
    try:
        user_uuid = uuid.UUID(current_user_id)
        
        result = await AuthenticationService.change_password(
            user_id=user_uuid,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if result["success"]:
            return MessageResponse(message=result["message"])
        else:
            # Handle different error types
            if "errors" in result:
                # Password validation errors
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": result["message"],
                        "errors": result["errors"]
                    }
                )
            else:
                # Other errors (wrong current password, etc.)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result["message"]
                )
        
    except ValueError as e:
        # UUID parsing error
        logger.error(f"Invalid user ID format: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    except HTTPException:
        # Re-raise HTTP exceptions (from above)
        raise
    except Exception as e:
        # Catch all other exceptions and log them
        logger.error(f"Unexpected error changing password: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(
    request: Request,
    forgot_data: ForgotPasswordRequest
) -> SuccessResponse:
    """
    Request password reset
    
    Args:
        request: FastAPI request object
        forgot_data: Email for password reset
        
    Returns:
        Success confirmation
    """
    ip_address = get_client_ip(request)
    
    result = await AuthenticationService.request_password_reset(
        email=forgot_data.email,
        ip_address=ip_address
    )
    
    return SuccessResponse(
        message=result["message"],
        data=None
    )


@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(
    request: Request,
    reset_data: ResetPasswordRequest
) -> SuccessResponse:
    """
    Reset password with token
    
    Args:
        request: FastAPI request object
        reset_data: Reset token and new password
        
    Returns:
        Success confirmation
    """
    ip_address = get_client_ip(request)
    
    result = await AuthenticationService.reset_password(
        token=reset_data.token,
        new_password=reset_data.new_password,
        ip_address=ip_address
    )
    
    return SuccessResponse(
        message=result["message"],
        data=None
    )


@router.post("/verify-email", response_model=SuccessResponse)
async def verify_email(
    verification_data: EmailVerificationRequest
) -> SuccessResponse:
    """
    Verify user's email address
    
    Args:
        verification_data: Email verification token
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If verification fails
    """
    result = await AuthenticationService.verify_email(verification_data.token)
    
    return SuccessResponse(
        message=result["message"],
        data=result.get("user")
    )


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_email(
    request: Request
) -> MessageResponse:
    """
    Resend email verification link
    
    Args:
        request: FastAPI request object
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If resend fails
    """
    try:
        # Log raw request body for debugging
        import logging
        import json
        logger = logging.getLogger(__name__)
        
        # Get raw body for debugging
        body = await request.body()
        logger.error(f"Raw request body: {body}")
        
        try:
            body_dict = json.loads(body)
            logger.error(f"Parsed body: {body_dict}")
            
            if 'email' not in body_dict:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Missing 'email' field in request"
                )
            
            # Validate email format
            resend_data = ResendVerificationRequest(email=body_dict['email'])
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid JSON format"
            )
        except Exception as e:
            logger.error(f"Validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Request validation failed: {str(e)}"
            )
        
        logger.error(f"Processing resend verification for email: {resend_data.email}")
        result = await AuthenticationService.resend_verification_email(resend_data.email)
        return MessageResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Resend verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resend verification failed: {str(e)}"
        )


@router.post("/validate-email", response_model=EmailValidationResponse)
async def validate_email(
    validation_data: EmailValidationRequest
) -> EmailValidationResponse:
    """
    Validate email address format and deliverability
    
    Performs comprehensive email validation including:
    - Format validation
    - Domain existence checking
    - Disposable email detection
    - Typo suggestions
    - MX record verification
    
    Args:
        validation_data: Email validation request containing email to validate
        
    Returns:
        Email validation result with details
        
    Raises:
        HTTPException: If validation service fails
    """
    try:
        validation_service = EmailValidationService()
        result = await validation_service.validate_email_comprehensive(validation_data.email)
        
        return EmailValidationResponse(
            is_valid=result.is_valid,
            reason=result.reason,
            suggestion=result.suggestion,
            domain=result.domain,
            normalized_email=result.normalized_email
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email validation service error: {str(e)}"
        )


@router.post("/validate-password", response_model=PasswordValidationResponse)
async def check_password_strength(
    validation_data: PasswordValidationRequest
) -> PasswordValidationResponse:
    """
    Validate password strength and requirements
    
    Performs comprehensive password validation including:
    - Length requirements
    - Character complexity (uppercase, lowercase, numbers, symbols)
    - Common password detection
    - Pattern analysis (no 123, abc, qwerty patterns)
    - Personalized checks (no email parts in password)
    - Strength scoring and crack time estimation
    
    Args:
        validation_data: Password validation request
        
    Returns:
        Detailed password validation result with suggestions
        
    Raises:
        HTTPException: If validation service fails
    """
    try:
        password_service = PasswordValidationService()
        result = password_service.validate_password(
            password=validation_data.password,
            email=validation_data.email
        )
        
        # Convert PasswordRequirement objects to PasswordRequirementCheck
        requirement_checks = [
            PasswordRequirementCheck(
                name=req.name,
                description=req.description,
                is_met=req.is_met
            )
            for req in result.requirements
        ]
        
        return PasswordValidationResponse(
            is_valid=result.is_valid,
            strength_score=result.strength_score,
            strength_level=result.strength_level,
            requirements=requirement_checks,
            suggestions=result.suggestions,
            estimated_crack_time=result.estimated_crack_time
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password validation service error: {str(e)}"
        )


@router.post("/verify-email", response_model=EmailVerificationResponse)
async def verify_email_endpoint(
    verification_data: EmailVerificationRequest
) -> EmailVerificationResponse:
    """
    Verify user's email address with verification token
    
    Validates the email verification token and marks the user's email as verified.
    This endpoint is typically called when a user clicks the verification link 
    in their welcome email.
    
    Args:
        verification_data: Email verification request with token
        
    Returns:
        Verification confirmation with user information
        
    Raises:
        HTTPException: If token is invalid or verification fails
    """
    try:
        result = await AuthenticationService.verify_email(
            verification_token=verification_data.token
        )
        return EmailVerificationResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email verification failed: {str(e)}"
        )



@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password_endpoint(
    request: Request,
    forgot_data: ForgotPasswordRequest
) -> MessageResponse:
    """
    Request password reset for user account
    
    Generates a password reset token and sends a reset link via email.
    The reset token expires after 1 hour for security.
    
    Args:
        request: FastAPI request object
        forgot_data: Forgot password request with email
        
    Returns:
        Confirmation that reset email was sent
        
    Raises:
        HTTPException: If email not found or sending fails
    """
    try:
        ip_address = get_client_ip(request)
        result = await AuthenticationService.request_password_reset(
            email=forgot_data.email,
            ip_address=ip_address
        )
        return MessageResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset request failed: {str(e)}"
        )


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password_endpoint(
    request: Request,
    reset_data: ResetPasswordRequest
) -> ResetPasswordResponse:
    """
    Reset user password with reset token
    
    Validates the password reset token and updates the user's password.
    The reset token can only be used once and expires after 1 hour.
    
    Args:
        request: FastAPI request object
        reset_data: Reset password request with token and new password
        
    Returns:
        Password reset confirmation with user information
        
    Raises:
        HTTPException: If token is invalid or reset fails
    """
    try:
        ip_address = get_client_ip(request)
        logger.info(f"Reset password request - Token: {reset_data.token[:10]}..., IP: {ip_address}")
        result = await AuthenticationService.reset_password(
            token=reset_data.token,
            new_password=reset_data.new_password,
            ip_address=ip_address
        )
        return ResetPasswordResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )


@router.get("/validate-reset-token", response_model=ValidateResetTokenResponse)
async def validate_reset_token_endpoint(
    token: str
) -> ValidateResetTokenResponse:
    """
    Validate password reset token
    
    Checks if a password reset token is valid and not expired.
    Used to verify tokens before showing the password reset form.
    
    Args:
        token: Password reset token to validate
        
    Returns:
        Token validation result with status
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        result = await AuthenticationService.validate_reset_token(token=token)
        return ValidateResetTokenResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token validation failed: {str(e)}"
        )

