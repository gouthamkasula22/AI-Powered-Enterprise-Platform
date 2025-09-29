"""
Authentication Use Cases

Core business workflows for user authentication, including registration,
login, logout, password management, and email verification.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets

logger = logging.getLogger(__name__)

from ..dto import (
    RegisterRequestDTO, LoginRequestDTO, LoginResponseDTO, 
    RefreshTokenRequestDTO, RefreshTokenResponseDTO,
    PasswordResetRequestDTO, PasswordResetConfirmDTO,
    ChangePasswordRequestDTO, EmailVerificationRequestDTO,
    MessageResponseDTO, user_entity_to_dto, UserDTO
)
from ..commands import (
    RegisterUserCommand, LoginUserCommand, RefreshTokenCommand,
    LogoutCommand, LogoutAllCommand, InitiatePasswordResetCommand,
    ConfirmPasswordResetCommand, ChangePasswordCommand,
    SendVerificationEmailCommand, VerifyEmailCommand
)
from ...domain.entities.user import User
from ...domain.value_objects.email import Email
from ...domain.value_objects.password import Password
from ...domain.repositories.user_repository import IUserRepository
from ...domain.exceptions import (
    UserNotFoundException, EmailAlreadyExistsException,
    InvalidCredentialsException, AccountNotVerifiedException,
    AccountDeactivatedException, ValidationError
)


class AuthenticationUseCases:
    """
    Authentication use cases handling all auth-related business workflows.
    
    This class orchestrates between domain entities, repositories, and
    infrastructure services to implement authentication features.
    """
    
    def __init__(
        self,
        user_repository: IUserRepository,
        auth_service,  # AuthenticationService from infrastructure
        email_service,  # EmailService from infrastructure  
        template_service  # EmailTemplateService from infrastructure
    ):
        self.user_repository = user_repository
        self.auth_service = auth_service
        self.email_service = email_service
        self.template_service = template_service
    
    async def register_user(self, request: RegisterRequestDTO) -> LoginResponseDTO:
        """
        Register a new user account.
        
        Business rules:
        - Email must be unique
        - Password must meet strength requirements
        - Send verification email after registration
        - Return login tokens for immediate access
        """
        
        # Check if user already exists
        email = Email(request.email)
        existing_user = await self.user_repository.find_by_email(email)
        if existing_user:
            raise EmailAlreadyExistsException(request.email)
        
        # Check username uniqueness if provided
        if request.username:
            existing_username = await self.user_repository.find_by_username(request.username)
            if existing_username:
                raise EmailAlreadyExistsException(f"Username {request.username} already exists")
        
        # Create password
        password = Password(request.password)
        
        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        # Create user entity
        user = User(
            email=email,
            username=request.username,
            password_hash=password.hash(),
            first_name=request.first_name,
            last_name=request.last_name,
            email_verification_token=verification_token,
            email_verification_expires=verification_expires
        )
        
        # Save user
        saved_user = await self.user_repository.save(user)
        
        # Send verification email
        await self._send_verification_email(saved_user)
        
        # Generate login tokens
        tokens = await self.auth_service.create_token_pair(
            saved_user.id, 
            saved_user.email.value if saved_user.email else "",
            role=saved_user.role.value if saved_user.role else 'USER'
        )
        
        return LoginResponseDTO(
            user=user_entity_to_dto(saved_user),
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"]
        )
    
    async def login_user(self, request: LoginRequestDTO) -> LoginResponseDTO:
        """
        Authenticate user and return tokens.
        
        Business rules:
        - Email and password must be valid
        - Account must be active
        - Update last login timestamp
        """
        
        # Find user by email
        email = Email(request.email)
        user = await self.user_repository.find_by_email(email)
        if not user:
            raise InvalidCredentialsException()
        
        # Check if account is active
        if not user.is_active:
            raise AccountDeactivatedException()
        
        # Verify password
        password_valid = False
        if user.password_hash:
            password_valid = Password.verify(user.password_hash, request.password)
            
        # Add detailed logging for debugging
        print(f"Login attempt for user: {user.email.value if user.email else 'unknown'}")
        print(f"Password hash exists: {bool(user.password_hash)}")
        print(f"Password valid: {password_valid}")
        
        if not user.password_hash or not password_valid:
            raise InvalidCredentialsException()
        
        # Update last login
        user.last_login = datetime.utcnow()
        await self.user_repository.save(user)
        
        # Generate tokens
        tokens = await self.auth_service.create_token_pair(
            user.id,
            user.email.value if user.email else "",
            role=user.role.value if user.role else 'USER'
        )
        
        return LoginResponseDTO(
            user=user_entity_to_dto(user),
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"]
        )
    
    async def refresh_token(self, request: RefreshTokenRequestDTO) -> RefreshTokenResponseDTO:
        """
        Refresh authentication tokens.
        
        Business rules:
        - Refresh token must be valid and not expired
        - Old refresh token is invalidated
        - Return new token pair
        """
        
        new_tokens = await self.auth_service.refresh_token(request.refresh_token)
        if not new_tokens:
            raise InvalidCredentialsException()
        
        return RefreshTokenResponseDTO(
            access_token=new_tokens["access_token"],
            refresh_token=new_tokens["refresh_token"],
            token_type=new_tokens.get("token_type", "bearer"),
            expires_in=new_tokens.get("expires_in", 1800)
        )
    
    async def logout_user(self, access_token: str) -> MessageResponseDTO:
        """
        Logout user by invalidating tokens.
        
        Business rules:
        - Blacklist the provided access token
        - Token becomes invalid immediately
        """
        
        success = await self.auth_service.logout_token(access_token)
        if not success:
            return MessageResponseDTO(
                message="Logout completed",
                success=True
            )
        
        return MessageResponseDTO(
            message="Successfully logged out",
            success=True
        )
    
    async def logout_all_devices(self, user_id: int) -> MessageResponseDTO:
        """
        Logout user from all devices.
        
        Business rules:
        - Invalidate all tokens for the user
        - User must re-authenticate on all devices
        """
        
        await self.auth_service.logout_all_user_tokens(user_id)
        
        return MessageResponseDTO(
            message="Successfully logged out from all devices",
            success=True
        )
    
    async def initiate_password_reset(self, request: PasswordResetRequestDTO) -> MessageResponseDTO:
        """
        Initiate password reset process.
        
        Business rules:
        - Generate reset token with expiration
        - Send reset email
        - Always return success (don't reveal if email exists)
        """
        
        email = Email(request.email)
        user = await self.user_repository.find_by_email(email)
        
        if user and user.is_active:
            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            reset_expires = datetime.utcnow() + timedelta(hours=1)
            
            # Update user with reset token
            user.password_reset_token = reset_token
            user.password_reset_expires = reset_expires
            await self.user_repository.save(user)
            
            # Send reset email
            await self._send_password_reset_email(user)
        
        # Always return success for security
        return MessageResponseDTO(
            message="If an account with that email exists, a password reset link has been sent",
            success=True
        )
    
    async def confirm_password_reset(self, request: PasswordResetConfirmDTO) -> MessageResponseDTO:
        """
        Confirm password reset with token.
        
        Business rules:
        - Token must be valid and not expired
        - Update password and clear reset token
        - Invalidate all user sessions
        """
        
        user = await self.user_repository.find_by_password_reset_token(request.token)
        if not user:
            raise ValidationError("Invalid or expired reset token")
        
        # Check token expiration
        if user.password_reset_expires and user.password_reset_expires < datetime.utcnow():
            raise ValidationError("Reset token has expired")
        
        # Update password
        new_password = Password(request.new_password)
        user.change_password(new_password)
        
        # Clear reset token
        user.password_reset_token = None
        user.password_reset_expires = None
        
        # Save changes
        await self.user_repository.save(user)
        
        # Invalidate all user sessions for security
        await self.auth_service.logout_all_user_tokens(user.id)
        
        return MessageResponseDTO(
            message="Password has been reset successfully",
            success=True
        )
    
    async def change_password(self, user_id: int, request: ChangePasswordRequestDTO) -> MessageResponseDTO:
        """
        Change user password.
        
        Business rules:
        - Current password must be correct
        - New password must meet requirements
        - Invalidate all other sessions for security
        """
        
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))
        
        # Verify current password
        if not user.password_hash or not Password.verify(user.password_hash, request.current_password):
            raise InvalidCredentialsException()
        
        # Update password
        new_password = Password(request.new_password)
        user.change_password(new_password)
        await self.user_repository.save(user)
        
        # Invalidate other sessions for security
        await self.auth_service.logout_all_user_tokens(user.id)
        
        return MessageResponseDTO(
            message="Password changed successfully",
            success=True
        )
    
    async def send_verification_email(self, user_id: int) -> MessageResponseDTO:
        """
        Send email verification to user.
        
        Business rules:
        - User must exist and be active
        - Generate new verification token
        - Send verification email
        """
        
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))
        
        if user.is_verified:
            return MessageResponseDTO(
                message="Email is already verified",
                success=True
            )
        
        # Generate new verification token
        verification_token = secrets.token_urlsafe(32)
        verification_expires = datetime.utcnow() + timedelta(hours=24)
        
        user.email_verification_token = verification_token
        user.email_verification_expires = verification_expires
        await self.user_repository.save(user)
        
        # Send verification email
        await self._send_verification_email(user)
        
        return MessageResponseDTO(
            message="Verification email sent successfully",
            success=True
        )
    
    async def verify_email(self, request: EmailVerificationRequestDTO) -> MessageResponseDTO:
        """
        Verify email with token.
        
        Business rules:
        - Token must be valid and not expired
        - Mark email as verified
        - Clear verification token
        """
        
        user = await self.user_repository.find_by_email_verification_token(request.token)
        if not user:
            raise ValidationError("Invalid or expired verification token")
        
        # Check token expiration
        if user.email_verification_expires and user.email_verification_expires < datetime.utcnow():
            raise ValidationError("Verification token has expired")
        
        # Verify email
        user.verify_email()
        await self.user_repository.save(user)
        
        # Send welcome email after successful verification
        await self._send_welcome_email(user)
        
        return MessageResponseDTO(
            message="Email verified successfully",
            success=True
        )
    
    async def _send_verification_email(self, user: User) -> None:
        """Send verification email to user"""
        if not user.email_verification_token:
            return
        
        if not user.email:
            logger.warning("User has no email address for verification email")
            return
        
        # Skip email sending if template service is not available
        if not self.template_service:
            logger.warning(f"Template service not available, skipping verification email for {user.email.value}")
            return
        
        display_name = user.display_name or f"{user.first_name or ''} {user.last_name or ''}".strip()
        if not display_name:
            display_name = user.email.value.split('@')[0]
        
        html_content, text_content = self.template_service.generate_verification_email(
            display_name,
            user.email_verification_token
        )
        
        from ...infrastructure.email import EmailMessage
        email_message = EmailMessage(
            to=[user.email.value],
            subject="Verify your email address",
            html_content=html_content,
            text_content=text_content
        )
        
        await self.email_service.send_email(email_message)
    
    async def get_current_user(self, access_token: str) -> UserDTO:
        """
        Get current user from access token
        
        Args:
            access_token: JWT access token
            
        Returns:
            UserDTO object for the current user
            
        Raises:
            ValidationError: If token is invalid or expired
            TokenBlacklistedException: If token has been blacklisted
            UserNotFoundException: If user not found
            AccountDeactivatedException: If user account is deactivated
        """
        from ...domain.exceptions.domain_exceptions import ValidationError, UserNotFoundException, AccountDeactivatedException
        from ...infrastructure.security.jwt_service import TokenType
        from ...domain.exceptions.auth_exceptions import TokenBlacklistedException
        
        # Validate token using the auth service
        token_data = await self.auth_service.validate_token(access_token, TokenType.ACCESS)
        
        if not token_data:
            # Check if token is blacklisted specifically
            is_blacklisted = await self.auth_service.is_token_blacklisted(access_token)
            if is_blacklisted:
                raise TokenBlacklistedException("Token has been blacklisted or revoked")
            raise ValidationError("Invalid or expired token")
        
        user_id = token_data.user_id
        if not user_id:
            raise ValidationError("Invalid token payload")
        
        # Get user from repository
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))
        
        # Check if user is active
        if not user.is_active:
            raise AccountDeactivatedException()
        
        # Convert to DTO
        return user_entity_to_dto(user)
    
    async def _send_password_reset_email(self, user: User) -> None:
        """Send password reset email to user"""
        try:
            if not user.email:
                print("❌ DEBUG: User has no email address")
                return
                
            print(f"🔧 DEBUG: Starting password reset email for user {user.email.value}")
            
            if not user.password_reset_token:
                print("❌ DEBUG: No password reset token found")
                return
            
            print(f"✅ DEBUG: Password reset token exists: {user.password_reset_token[:10]}...")
            
            display_name = user.display_name or f"{user.first_name or ''} {user.last_name or ''}".strip()
            if not display_name:
                display_name = user.email.value.split('@')[0]
            
            print(f"✅ DEBUG: Display name: {display_name}")
            
            print("🔧 DEBUG: Generating email templates...")
            html_content, text_content = self.template_service.generate_password_reset_email(
                display_name,
                user.password_reset_token
            )
            
            print(f"✅ DEBUG: Templates generated. HTML length: {len(html_content)}, Text length: {len(text_content)}")
            
            from ...infrastructure.email import EmailMessage
            email_message = EmailMessage(
                to=[user.email.value],
                subject="Reset your password",
                html_content=html_content,
                text_content=text_content
            )
            
            print(f"✅ DEBUG: Email message created for: {email_message.to}")
            print("📧 DEBUG: Calling email service...")
            
            result = await self.email_service.send_email(email_message)
            
            if result:
                print("✅ DEBUG: Email service returned success")
            else:
                print("❌ DEBUG: Email service returned failure")
                
        except Exception as e:
            print(f"❌ DEBUG: Error in _send_password_reset_email: {e}")
            import traceback
            traceback.print_exc()
            # Don't re-raise to avoid breaking the password reset flow
    
    async def _send_welcome_email(self, user: User) -> None:
        """Send welcome email to newly verified user"""
        
        if not user.email:
            print("❌ DEBUG: User has no email address for welcome email")
            return
        
        display_name = user.display_name or f"{user.first_name or ''} {user.last_name or ''}".strip()
        if not display_name:
            display_name = user.email.value.split('@')[0]
        
        html_content, text_content = self.template_service.generate_welcome_email(
            display_name
        )
        
        from ...infrastructure.email import EmailMessage
        email_message = EmailMessage(
            to=[user.email.value],
            subject="Welcome! Your account is now active",
            html_content=html_content,
            text_content=text_content
        )
        
        await self.email_service.send_email(email_message)