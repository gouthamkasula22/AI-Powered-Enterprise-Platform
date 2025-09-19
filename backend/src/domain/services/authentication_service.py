"""
Authentication Domain Service

Contains complex business logic for authentication that doesn't
belong in a single entity. Pure domain logic with no infrastructure dependencies.
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import Optional
from ..entities.user import User
from ..value_objects.email import Email
from ..value_objects.password import Password
from ..repositories.user_repository import IUserRepository
from ..exceptions.domain_exceptions import (
    InvalidCredentialsException,
    EmailAlreadyExistsException,
    UserNotFoundException,
    AccountDeactivatedException,
    AccountNotVerifiedException,
    ValidationError
)


class AuthenticationService:
    """
    Domain service for authentication-related business logic.
    
    Orchestrates complex business rules that span multiple entities
    or require repository access but remain pure domain logic.
    """
    
    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository
    
    async def register_user(
        self,
        email: Email,
        password: Password,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """
        Register a new user with business validation
        
        Args:
            email: User's email address
            password: User's password
            first_name: User's first name (optional)
            last_name: User's last name (optional)
            
        Returns:
            Created user entity
            
        Raises:
            EmailAlreadyExistsException: If email is already registered
            ValidationError: If validation fails
        """
        # Business rule: Email must be unique
        if await self._user_repository.exists_by_email(email):
            raise EmailAlreadyExistsException(email.value)
        
        # Create user entity
        user = User(
            email=email,
            password_hash=password.hash(),
            first_name=first_name.strip() if first_name else None,
            last_name=last_name.strip() if last_name else None,
            is_active=True,
            is_verified=False,  # Business rule: Require email verification
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Generate email verification token
        verification_token = self._generate_secure_token()
        verification_expires = datetime.utcnow() + timedelta(hours=24)
        user.set_verification_token(verification_token, verification_expires)
        
        # Save user
        return await self._user_repository.create(user)
    
    async def authenticate_user(self, email: Email, password: str) -> User:
        """
        Authenticate user credentials
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            Authenticated user entity
            
        Raises:
            InvalidCredentialsException: If credentials are invalid
            AccountDeactivatedException: If account is deactivated
            AccountNotVerifiedException: If account is not verified
        """
        # Find user by email
        user = await self._user_repository.find_by_email(email)
        if not user:
            raise InvalidCredentialsException()
        
        # Verify password
        if not user.password_hash or not Password.verify(user.password_hash, password):
            raise InvalidCredentialsException()
        
        # Business rule: Only active, verified users can login
        if not user.is_active:
            raise AccountDeactivatedException()
        
        if not user.is_verified:
            raise AccountNotVerifiedException()
        
        # Record successful login
        user.record_login()
        await self._user_repository.update(user)
        
        return user
    
    async def initiate_password_reset(self, email: Email) -> Optional[str]:
        """
        Initiate password reset process
        
        Args:
            email: User's email address
            
        Returns:
            Reset token if user exists, None otherwise (security: don't reveal if email exists)
        """
        user = await self._user_repository.find_by_email(email)
        if not user or not user.is_active:
            # Security: Don't reveal whether email exists
            return None
        
        # Generate reset token
        reset_token = self._generate_secure_token()
        reset_expires = datetime.utcnow() + timedelta(hours=1)  # Short expiration for security
        
        user.set_password_reset_token(reset_token, reset_expires)
        await self._user_repository.update(user)
        
        return reset_token
    
    async def reset_password(self, token: str, new_password: Password) -> User:
        """
        Reset password using token
        
        Args:
            token: Password reset token
            new_password: New password
            
        Returns:
            Updated user entity
            
        Raises:
            ValidationError: If token is invalid or expired
            UserNotFoundException: If user not found
        """
        user = await self._user_repository.find_by_password_reset_token(token)
        if not user:
            raise ValidationError("Invalid or expired reset token")
        
        if not user.is_password_reset_token_valid:
            raise ValidationError("Reset token has expired")
        
        # Change password and clear reset token
        user.change_password(new_password)
        user.clear_password_reset_token()
        
        return await self._user_repository.update(user)
    
    async def verify_email(self, token: str) -> User:
        """
        Verify user's email address
        
        Args:
            token: Email verification token
            
        Returns:
            Updated user entity
            
        Raises:
            ValidationError: If token is invalid or expired
            UserNotFoundException: If user not found
        """
        user = await self._user_repository.find_by_verification_token(token)
        if not user:
            raise ValidationError("Invalid or expired verification token")
        
        if not user.is_email_verification_token_valid:
            raise ValidationError("Verification token has expired")
        
        # Verify email
        user.verify_email()
        
        return await self._user_repository.update(user)
    
    async def resend_verification_email(self, email: Email) -> Optional[str]:
        """
        Resend email verification token
        
        Args:
            email: User's email address
            
        Returns:
            New verification token if user exists and is unverified, None otherwise
        """
        user = await self._user_repository.find_by_email(email)
        if not user or not user.is_active or user.is_verified:
            return None
        
        # Generate new verification token
        verification_token = self._generate_secure_token()
        verification_expires = datetime.utcnow() + timedelta(hours=24)
        user.set_verification_token(verification_token, verification_expires)
        
        await self._user_repository.update(user)
        return verification_token
    
    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: Password
    ) -> User:
        """
        Change user's password
        
        Args:
            user_id: User's ID
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            Updated user entity
            
        Raises:
            UserNotFoundException: If user not found
            InvalidCredentialsException: If current password is incorrect
            AccountDeactivatedException: If account is deactivated
        """
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))
        
        # Verify current password
        if not user.password_hash or not Password.verify(user.password_hash, current_password):
            raise InvalidCredentialsException()
        
        # Change password
        user.change_password(new_password)
        
        return await self._user_repository.update(user)
    
    def _generate_secure_token(self, length: int = 32) -> str:
        """
        Generate cryptographically secure token
        
        Args:
            length: Token length
            
        Returns:
            Secure random token
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))