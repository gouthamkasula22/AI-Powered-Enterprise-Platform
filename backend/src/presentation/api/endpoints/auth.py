"""
Authentication Endpoints

FastAPI routes for user authentication operations.
Integrates with application layer use cases.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from typing import Dict, Any

logger = logging.getLogger(__name__)

from ....application.dto import (
    RegisterRequestDTO, LoginRequestDTO, LoginResponseDTO,
    RefreshTokenRequestDTO, RefreshTokenResponseDTO,
    PasswordResetRequestDTO, PasswordResetConfirmDTO,
    ChangePasswordRequestDTO, EmailVerificationRequestDTO,
    MessageResponseDTO, UserDTO
)
from ....application.use_cases.auth_use_cases import AuthenticationUseCases
from ....domain.exceptions.domain_exceptions import (
    UserNotFoundException, EmailAlreadyExistsException,
    InvalidCredentialsException, ValidationError, UserAlreadyExistsError
)
from ..dependencies.auth import get_current_user, get_auth_use_cases
from ..schemas.auth import (
    RegisterRequest, LoginRequest, RefreshTokenRequest,
    PasswordResetRequest, PasswordResetConfirm, ChangePasswordRequest,
    EmailVerificationRequest, AuthResponse, MessageResponse,
    EmailValidationResponse, PasswordValidationResponse
)

router = APIRouter()
security = HTTPBearer()


@router.post("/register", 
             response_model=AuthResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Register new user",
             description="Create a new user account with email verification")
async def register_user(
    request: RegisterRequest,
    background_tasks: BackgroundTasks,
    auth_use_cases: AuthenticationUseCases = Depends(get_auth_use_cases)
) -> AuthResponse:
    """
    Register a new user account
    
    - **email**: Valid email address
    - **password**: Strong password meeting requirements
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **display_name**: Optional display name
    """
    try:
        # Convert Pydantic model to DTO
        register_dto = RegisterRequestDTO(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            username=request.username
        )
        
        # Execute use case
        result = await auth_use_cases.register_user(register_dto)
        
        return AuthResponse(
            user=result.user,
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            token_type=result.token_type,
            message="Registration successful. Please verify your email."
        )
        
    except EmailAlreadyExistsException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "EMAIL_EXISTS", "message": str(e)}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "VALIDATION_ERROR", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Registration failed with unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "REGISTRATION_FAILED", "message": "Registration failed due to server error"}
        )


@router.post("/login",
             response_model=AuthResponse,
             status_code=status.HTTP_200_OK,
             summary="User login",
             description="Authenticate user and return access tokens")
async def login_user(
    request: LoginRequest,
    auth_use_cases: AuthenticationUseCases = Depends(get_auth_use_cases)
) -> AuthResponse:
    """
    Authenticate user with email and password
    
    - **email**: User's email address
    - **password**: User's password
    """
    try:
        # Convert to DTO
        login_dto = LoginRequestDTO(
            email=request.email,
            password=request.password
        )
        
        # Execute use case
        result = await auth_use_cases.login_user(login_dto)
        
        return AuthResponse(
            user=result.user,
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            token_type=result.token_type,
            message="Login successful"
        )
        
    except InvalidCredentialsException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "INVALID_CREDENTIALS", "message": "Invalid email or password"}
        )
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "INVALID_CREDENTIALS", "message": "Invalid email or password"}
        )


@router.post("/logout",
             response_model=MessageResponse,
             status_code=status.HTTP_200_OK,
             summary="User logout",
             description="Logout user and invalidate tokens")
async def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: UserDTO = Depends(get_current_user),
    auth_use_cases: AuthenticationUseCases = Depends(get_auth_use_cases)
) -> MessageResponse:
    """
    Logout user and invalidate access token
    """
    try:
        access_token = credentials.credentials
        result = await auth_use_cases.logout_user(access_token)
        
        return MessageResponse(message=result.message)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "LOGOUT_ERROR", "message": "Failed to logout"}
        )


@router.post("/refresh",
             response_model=RefreshTokenResponseDTO,
             status_code=status.HTTP_200_OK,
             summary="Refresh access token",
             description="Get new access token using refresh token")
async def refresh_token(
    request: RefreshTokenRequest,
    auth_use_cases: AuthenticationUseCases = Depends(get_auth_use_cases)
) -> RefreshTokenResponseDTO:
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    """
    try:
        # Convert to DTO
        refresh_dto = RefreshTokenRequestDTO(
            refresh_token=request.refresh_token
        )
        
        # Execute use case
        result = await auth_use_cases.refresh_token(refresh_dto)
        
        return result
        
    except InvalidCredentialsException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "INVALID_REFRESH_TOKEN", "message": "Invalid or expired refresh token"}
        )


@router.post("/verify-email",
             response_model=MessageResponse,
             status_code=status.HTTP_200_OK,
             summary="Verify email address",
             description="Verify user email with verification token")
async def verify_email(
    request: EmailVerificationRequest,
    auth_use_cases: AuthenticationUseCases = Depends(get_auth_use_cases)
) -> MessageResponse:
    """
    Verify user email address
    
    - **token**: Email verification token
    """
    try:
        # Convert to DTO
        verify_dto = EmailVerificationRequestDTO(
            token=request.token
        )
        
        # Execute use case
        result = await auth_use_cases.verify_email(verify_dto)
        
        return MessageResponse(message=result.message)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_TOKEN", "message": str(e)}
        )


@router.post("/forgot-password",
             response_model=MessageResponse,
             status_code=status.HTTP_200_OK,
             summary="Request password reset",
             description="Send password reset email to user")
async def forgot_password(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    auth_use_cases: AuthenticationUseCases = Depends(get_auth_use_cases)
) -> MessageResponse:
    """
    Request password reset
    
    - **email**: User's email address
    """
    try:
        # Convert to DTO
        reset_dto = PasswordResetRequestDTO(
            email=request.email
        )
        
        # Execute use case
        result = await auth_use_cases.initiate_password_reset(reset_dto)
        
        return MessageResponse(message=result.message)
        
    except UserNotFoundException:
        # Don't reveal if email exists - return success anyway
        return MessageResponse(
            message="If the email exists, a password reset link has been sent."
        )


@router.post("/reset-password",
             response_model=MessageResponse,
             status_code=status.HTTP_200_OK,
             summary="Reset password",
             description="Reset password using reset token")
async def reset_password(
    request: PasswordResetConfirm,
    auth_use_cases: AuthenticationUseCases = Depends(get_auth_use_cases)
) -> MessageResponse:
    """
    Reset password using reset token
    
    - **token**: Password reset token
    - **new_password**: New password
    """
    try:
        # Convert to DTO
        confirm_dto = PasswordResetConfirmDTO(
            token=request.token,
            new_password=request.new_password
        )
        
        # Execute use case
        result = await auth_use_cases.confirm_password_reset(confirm_dto)
        
        return MessageResponse(message=result.message)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_TOKEN", "message": str(e)}
        )


@router.get("/validate-token",
             response_model=MessageResponse,
             status_code=status.HTTP_200_OK,
             summary="Validate auth token",
             description="Validates if the current token is valid and active")
async def check_token_validity(
    current_user: UserDTO = Depends(get_current_user)
) -> MessageResponse:
    """
    Validate the current auth token
    
    Used by frontend to check if session is still valid
    """
    return MessageResponse(
        message="Token is valid",
        success=True
    )


@router.post("/change-password",
             response_model=MessageResponse,
             status_code=status.HTTP_200_OK,
             summary="Change password",
             description="Change user password (requires authentication)")
async def change_password(
    request: ChangePasswordRequest,
    current_user: UserDTO = Depends(get_current_user),
    auth_use_cases: AuthenticationUseCases = Depends(get_auth_use_cases)
) -> MessageResponse:
    """
    Change user password
    
    - **current_password**: Current password
    - **new_password**: New password
    """
    try:
        # Convert to DTO
        change_dto = ChangePasswordRequestDTO(
            user_id=current_user.id,
            current_password=request.current_password,
            new_password=request.new_password
        )
        
        # Execute use case
        result = await auth_use_cases.change_password(current_user.id, change_dto)
        
        return MessageResponse(message=result.message)
        
    except InvalidCredentialsException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_PASSWORD", "message": "Current password is incorrect"}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "VALIDATION_ERROR", "message": str(e)}
        )


@router.post("/validate-email",
             response_model=EmailValidationResponse,
             status_code=status.HTTP_200_OK,
             summary="Validate email address",
             description="Check if email format is valid and available")
async def validate_email(
    request: dict,
    auth_use_cases: AuthenticationUseCases = Depends(get_auth_use_cases)
) -> EmailValidationResponse:
    """
    Validate email address format and availability
    
    - **email**: Email address to validate
    """
    try:
        email = request.get("email", "").strip()
        if not email:
            return EmailValidationResponse(
                is_valid=False,
                message="Email is required",
                reason="MISSING_EMAIL",
                suggestion=None
            )
        
        # Validate email format
        from ....domain.value_objects.email import Email
        try:
            email_obj = Email(email)
            # Check if email already exists
            try:
                existing_user = await auth_use_cases.user_repository.find_by_email(email_obj)
                if existing_user:
                    return EmailValidationResponse(
                        is_valid=False,
                        message="Email already registered",
                        reason="EMAIL_EXISTS",
                        suggestion=None
                    )
            except Exception:
                pass  # User not found, email is available
            
            return EmailValidationResponse(
                is_valid=True,
                message="Email format is valid and available",
                suggestion=None,
                reason=None
            )
        except ValueError as e:
            return EmailValidationResponse(
                is_valid=False,
                message=str(e),
                reason="INVALID_FORMAT",
                suggestion=None
            )
        
    except Exception as e:
        return EmailValidationResponse(
            is_valid=False,
            message="Validation error occurred",
            reason="VALIDATION_ERROR",
            suggestion=None
        )


@router.post("/validate-password",
             response_model=PasswordValidationResponse,
             status_code=status.HTTP_200_OK,
             summary="Validate password strength",
             description="Check if password meets security requirements")
async def validate_password(
    request: dict
) -> PasswordValidationResponse:
    """
    Validate password strength requirements
    
    - **password**: Password to validate
    """
    try:
        password = request.get("password", "")
        if not password:
            return PasswordValidationResponse(
                is_valid=False,
                strength_score=0,
                strength_level="Very Weak",
                requirements=[],
                suggestions=["Password is required"],
                estimated_crack_time="N/A"
            )
        
        # Validate password strength
        from ....domain.value_objects.password import Password
        try:
            password_obj = Password(password)
            
            # Calculate strength metrics
            requirements = []
            suggestions = []
            
            # Check requirements
            if len(password) >= 8:
                requirements.append("At least 8 characters")
            else:
                suggestions.append("Use at least 8 characters")
                
            if any(c.isupper() for c in password):
                requirements.append("Contains uppercase letter")
            else:
                suggestions.append("Add an uppercase letter")
                
            if any(c.islower() for c in password):
                requirements.append("Contains lowercase letter")
            else:
                suggestions.append("Add a lowercase letter")
                
            if any(c.isdigit() for c in password):
                requirements.append("Contains number")
            else:
                suggestions.append("Add a number")
                
            if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
                requirements.append("Contains special character")
            else:
                suggestions.append("Add a special character")
            
            # Calculate strength score (0-4)
            strength_score = len(requirements)
            
            # Determine strength level
            if strength_score == 0:
                strength_level = "Very Weak"
            elif strength_score == 1:
                strength_level = "Weak"
            elif strength_score == 2:
                strength_level = "Fair"
            elif strength_score == 3:
                strength_level = "Good"
            elif strength_score == 4:
                strength_level = "Strong"
            else:
                strength_level = "Very Strong"
            
            # Estimate crack time
            if len(password) < 6:
                crack_time = "Less than 1 second"
            elif len(password) < 8:
                crack_time = "Several minutes"
            elif strength_score >= 4:
                crack_time = "Several years"
            else:
                crack_time = "Several days"
            
            return PasswordValidationResponse(
                is_valid=True,
                strength_score=strength_score,
                strength_level=strength_level,
                requirements=requirements,
                suggestions=suggestions,
                estimated_crack_time=crack_time
            )
            
        except ValueError as e:
            return PasswordValidationResponse(
                is_valid=False,
                strength_score=0,
                strength_level="Invalid",
                requirements=[],
                suggestions=[str(e)],
                estimated_crack_time="N/A"
            )
        
    except Exception as e:
        return PasswordValidationResponse(
            is_valid=False,
            strength_score=0,
            strength_level="Error",
            requirements=[],
            suggestions=["Validation error occurred"],
            estimated_crack_time="N/A"
        )


# Simple OAuth Implementation
from ....infrastructure.oauth.simple_google_oauth import SimpleGoogleOAuth
from ....infrastructure.database.repositories import SqlUserRepository
from ....infrastructure.security.jwt_service import AuthenticationService
from ....domain.value_objects.email import Email
from ....domain.value_objects.auth_method import AuthMethod
from ....domain.entities.user import User
from ..dependencies.auth import get_user_repository, get_auth_service


@router.get("/oauth/google/login")
async def google_oauth_login(redirect_uri: str = "http://localhost:8000/api/auth/oauth/google/callback"):
    """
    Start Google OAuth flow
    """
    try:
        oauth_service = SimpleGoogleOAuth()
        auth_url, state = oauth_service.get_authorization_url(redirect_uri)
        
        # Redirect to Google OAuth
        return RedirectResponse(url=auth_url, status_code=302)
        
    except Exception as e:
        logger.error(f"OAuth login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "OAUTH_ERROR", "message": "Failed to start OAuth flow"}
        )


@router.get("/oauth/google/callback")
async def google_oauth_callback(
    code: str,
    state: str,
    user_repo: SqlUserRepository = Depends(get_user_repository),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """
    Handle Google OAuth callback - the magic happens here!
    """
    # Simple deduplication using state parameter
    import hashlib
    request_key = f"oauth_callback_{hashlib.md5(f'{code}_{state}'.encode()).hexdigest()}"
    
    try:
        oauth_service = SimpleGoogleOAuth()
        redirect_uri = "http://localhost:8000/api/auth/oauth/google/callback"
        
        # Exchange code for access token
        access_token = await oauth_service.exchange_code_for_token(code, redirect_uri)
        
        # Get user info from Google
        google_user = await oauth_service.get_user_info(access_token)
        
        # Check if user already exists
        email = Email(google_user.email)
        existing_user = await user_repo.find_by_email(email)
        
        # Debug: Let's also do a raw database query to see what's really there
        from sqlalchemy import text
        debug_result = await user_repo.session.execute(
            text("SELECT id, email, auth_method FROM users WHERE email = :email"),
            {"email": google_user.email}
        )
        debug_rows = debug_result.fetchall()
        logger.info(f"Debug - Raw DB query found {len(debug_rows)} rows for email {google_user.email}")
        for row in debug_rows:
            logger.info(f"Debug - Found user: id={row[0]}, email='{row[1]}', auth_method='{row[2]}'")
        
        if existing_user:
            # USER EXISTS - Just login
            logger.info(f"OAuth login for existing user: {google_user.email}")
            
            # Update last login time
            existing_user.record_login()
            await user_repo.update(existing_user)
            
            # Generate JWT tokens
            token_pair = await auth_service.create_token_pair(
                user_id=existing_user.id or 0,
                email=existing_user.email.value if existing_user.email else ""
            )
            
            user_dto = UserDTO(
                id=existing_user.id or 0,
                email=existing_user.email.value if existing_user.email else "",
                first_name=existing_user.first_name,
                last_name=existing_user.last_name,
                display_name=existing_user.display_name,
                profile_picture_url=existing_user.profile_picture_url,
                is_verified=existing_user.is_verified,
                is_active=existing_user.is_active,
                created_at=existing_user.created_at,
                updated_at=existing_user.updated_at
            )
            
        else:
            # USER DOESN'T EXIST - Create new OAuth user with atomic upsert
            logger.info(f"Creating new OAuth user: {google_user.email}")
            
            # Create auth method for Google OAuth
            auth_method = AuthMethod.google_oauth(google_user.id)
            
            # Create new user
            new_user = User.create_from_oauth(
                email=email,
                auth_method=auth_method,
                first_name=google_user.given_name or "",
                last_name=google_user.family_name or "",
                display_name=google_user.name or google_user.email.split('@')[0],
                profile_picture_url=google_user.picture or "",
                is_verified=google_user.verified_email,
                is_active=True
            )
            
            # Try atomic upsert: insert if not exists, otherwise get existing
            user_for_tokens = None
            try:
                saved_user = await user_repo.save(new_user)
                logger.info(f"Created new OAuth user: {saved_user.id}")
                user_for_tokens = saved_user
                
            except UserAlreadyExistsError:
                # Concurrent request created the user - just get it
                logger.info(f"User created by concurrent request, fetching: {google_user.email}")
                
                # Wait a tiny bit for the other transaction to commit
                import asyncio
                await asyncio.sleep(0.05)
                
                existing_user = await user_repo.find_by_email(email)
                if existing_user:
                    logger.info(f"Found user created by concurrent request: {existing_user.id}")
                    user_for_tokens = existing_user
                else:
                    # If we still can't find it, something is very wrong
                    logger.error(f"Could not find user after concurrent creation: {google_user.email}")
                    raise Exception("OAuth user creation failed - please try again")
            
            # Generate JWT tokens
            token_pair = await auth_service.create_token_pair(
                user_id=user_for_tokens.id or 0,
                email=user_for_tokens.email.value if user_for_tokens.email else ""
            )
            
            user_dto = UserDTO(
                id=user_for_tokens.id or 0,
                email=user_for_tokens.email.value if user_for_tokens.email else "",
                first_name=user_for_tokens.first_name,
                last_name=user_for_tokens.last_name,
                display_name=user_for_tokens.display_name,
                profile_picture_url=user_for_tokens.profile_picture_url,
                is_verified=user_for_tokens.is_verified,
                is_active=user_for_tokens.is_active,
                created_at=user_for_tokens.created_at,
                updated_at=user_for_tokens.updated_at
            )
        
        # Redirect to frontend with success
        from ....shared.config import get_settings
        settings = get_settings()
        frontend_url = settings.frontend_url or "http://localhost:3000"
        
        success_url = (
            f"{frontend_url}/auth/callback"
            f"?success=true"
            f"&access_token={token_pair['access_token']}"
            f"&refresh_token={token_pair['refresh_token']}"
            f"&user_id={user_dto.id}"
            f"&email={user_dto.email}"
            f"&display_name={user_dto.display_name or user_dto.email}"
        )
        
        return RedirectResponse(url=success_url, status_code=302)
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        
        # Redirect to frontend with error
        from ....shared.config import get_settings
        settings = get_settings()
        frontend_url = settings.frontend_url or "http://localhost:3000"
        error_url = f"{frontend_url}/auth/callback?error=oauth_error&error_description={str(e)}"
        return RedirectResponse(url=error_url, status_code=302)


@router.get("/validate-token",
           response_model=MessageResponse,
           status_code=status.HTTP_200_OK,
           summary="Validate authentication token",
           description="Validates current authentication token and returns success if valid")
async def validate_token(
    current_user: UserDTO = Depends(get_current_user)
) -> MessageResponse:
    """
    Validate the current authentication token
    
    This endpoint is used by the frontend to periodically check if the current token is still valid.
    If the token has been blacklisted or is invalid, this will result in a 401 error.
    
    Returns:
        MessageResponse: Success message if token is valid
    
    Raises:
        HTTPException: 401 if token is invalid or blacklisted
    """
    return MessageResponse(
        message="Token is valid",
        success=True
    )

