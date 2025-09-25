"""
Application Services

High-level application services that coordinate multiple use cases
and provide unified interfaces for complex business operations.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from ..dto import (
    RegisterRequestDTO, LoginRequestDTO, LoginResponseDTO,
    RefreshTokenRequestDTO, RefreshTokenResponseDTO,
    PasswordResetRequestDTO, PasswordResetConfirmDTO,
    ChangePasswordRequestDTO, EmailVerificationRequestDTO,
    UpdateProfileRequestDTO, UpdateUserProfileRequestDTO, UserDTO, MessageResponseDTO,
    PaginationRequestDTO, PaginatedResponseDTO, UserListQueryDTO, UserListResponseDTO
)
from ..use_cases import AuthenticationUseCases, UserManagementUseCases
from ...domain.exceptions import DomainException

# Import chat service
from .enhanced_chat_service import EnhancedChatService

# Include EnhancedChatService in __all__
__all__ = [
    "UserService", 
    "EnhancedChatService"
]


class AuthenticationService:
    """
    High-level authentication service coordinating auth workflows.
    
    Provides a unified interface for all authentication operations
    and handles cross-cutting concerns like logging and metrics.
    """
    
    def __init__(self, auth_use_cases: AuthenticationUseCases):
        self.auth_use_cases = auth_use_cases
    
    async def register(self, request: RegisterRequestDTO) -> LoginResponseDTO:
        """Register a new user and return login response"""
        try:
            return await self.auth_use_cases.register_user(request)
        except DomainException:
            raise
        except Exception as e:
            # Log unexpected errors
            print(f"Unexpected error during registration: {e}")
            raise DomainException("Registration failed")
    
    async def login(self, request: LoginRequestDTO) -> LoginResponseDTO:
        """Authenticate user and return tokens"""
        try:
            return await self.auth_use_cases.login_user(request)
        except DomainException:
            raise
        except Exception as e:
            print(f"Unexpected error during login: {e}")
            raise DomainException("Login failed")
    
    async def refresh_tokens(self, request: RefreshTokenRequestDTO) -> RefreshTokenResponseDTO:
        """Refresh authentication tokens"""
        try:
            return await self.auth_use_cases.refresh_token(request)
        except DomainException:
            raise
        except Exception as e:
            print(f"Unexpected error during token refresh: {e}")
            raise DomainException("Token refresh failed")
    
    async def logout(self, access_token: str) -> MessageResponseDTO:
        """Logout user from current session"""
        try:
            return await self.auth_use_cases.logout_user(access_token)
        except Exception as e:
            print(f"Error during logout: {e}")
            # Return success even on error - logout should always succeed
            return MessageResponseDTO(message="Logout completed", success=True)
    
    async def logout_all_devices(self, user_id: int) -> MessageResponseDTO:
        """Logout user from all devices"""
        try:
            return await self.auth_use_cases.logout_all_devices(user_id)
        except Exception as e:
            print(f"Error during logout all: {e}")
            return MessageResponseDTO(message="Logout completed", success=True)
    
    async def request_password_reset(self, request: PasswordResetRequestDTO) -> MessageResponseDTO:
        """Initiate password reset process"""
        try:
            return await self.auth_use_cases.initiate_password_reset(request)
        except Exception as e:
            print(f"Error during password reset request: {e}")
            # Always return success for security
            return MessageResponseDTO(
                message="If an account with that email exists, a password reset link has been sent",
                success=True
            )
    
    async def confirm_password_reset(self, request: PasswordResetConfirmDTO) -> MessageResponseDTO:
        """Confirm password reset with token"""
        try:
            return await self.auth_use_cases.confirm_password_reset(request)
        except DomainException:
            raise
        except Exception as e:
            print(f"Unexpected error during password reset: {e}")
            raise DomainException("Password reset failed")
    
    async def change_password(self, user_id: int, request: ChangePasswordRequestDTO) -> MessageResponseDTO:
        """Change user password"""
        try:
            return await self.auth_use_cases.change_password(user_id, request)
        except DomainException:
            raise
        except Exception as e:
            print(f"Unexpected error during password change: {e}")
            raise DomainException("Password change failed")
    
    async def send_verification_email(self, user_id: int) -> MessageResponseDTO:
        """Send email verification"""
        try:
            return await self.auth_use_cases.send_verification_email(user_id)
        except DomainException:
            raise
        except Exception as e:
            print(f"Error sending verification email: {e}")
            return MessageResponseDTO(
                message="Verification email sent successfully",
                success=True
            )
    
    async def verify_email(self, request: EmailVerificationRequestDTO) -> MessageResponseDTO:
        """Verify email with token"""
        try:
            return await self.auth_use_cases.verify_email(request)
        except DomainException:
            raise
        except Exception as e:
            print(f"Unexpected error during email verification: {e}")
            raise DomainException("Email verification failed")


class UserService:
    """
    High-level user management service.
    
    Coordinates user management workflows and provides
    unified interfaces for user operations.
    """
    
    def __init__(self, user_use_cases: UserManagementUseCases):
        self.user_use_cases = user_use_cases
    
    async def get_profile(self, user_id: int) -> UserDTO:
        """Get user profile"""
        try:
            return await self.user_use_cases.get_user_profile(user_id)
        except DomainException:
            raise
        except Exception as e:
            print(f"Unexpected error getting user profile: {e}")
            raise DomainException("Failed to get user profile")
    
    async def update_profile(self, user_id: int, request: UpdateProfileRequestDTO) -> UserDTO:
        """Update user profile"""
        try:
            # Convert to the expected DTO
            update_request = UpdateUserProfileRequestDTO(
                user_id=user_id,
                username=None,  # Not being updated in this context
                first_name=request.first_name,
                last_name=request.last_name,
                display_name=request.display_name,
                bio=request.bio,
                phone_number=request.phone_number
            )
            return await self.user_use_cases.update_user_profile(update_request)
        except DomainException:
            raise
        except Exception as e:
            print(f"Unexpected error updating profile: {e}")
            raise DomainException("Profile update failed")
    
    async def update_profile_picture(self, user_id: int, profile_picture_url: str) -> UserDTO:
        """Update profile picture"""
        try:
            return await self.user_use_cases.update_profile_picture(user_id, profile_picture_url)
        except DomainException:
            raise
        except Exception as e:
            print(f"Unexpected error updating profile picture: {e}")
            raise DomainException("Profile picture update failed")
    
    async def deactivate_account(self, user_id: int) -> MessageResponseDTO:
        """Deactivate user account"""
        try:
            return await self.user_use_cases.deactivate_account(user_id)
        except DomainException:
            raise
        except Exception as e:
            print(f"Unexpected error deactivating account: {e}")
            raise DomainException("Account deactivation failed")
    
    async def reactivate_account(self, user_id: int) -> MessageResponseDTO:
        """Reactivate user account"""
        try:
            return await self.user_use_cases.reactivate_account(user_id)
        except DomainException:
            raise
        except Exception as e:
            print(f"Unexpected error reactivating account: {e}")
            raise DomainException("Account reactivation failed")
    
    async def list_users(
        self,
        pagination: PaginationRequestDTO,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        search: Optional[str] = None
    ) -> UserListResponseDTO:
        """List users with filtering and pagination"""
        try:
            # Create UserListQueryDTO from pagination and filter parameters
            query = UserListQueryDTO(
                page=pagination.page,
                limit=pagination.size,
                search=search,
                is_active=is_active,
                is_verified=is_verified
            )
            return await self.user_use_cases.list_users(query)
        except Exception as e:
            print(f"Error listing users: {e}")
            # Return empty list on error
            return UserListResponseDTO(
                users=[],
                total=0,
                page=pagination.page,
                limit=pagination.size,
                pages=0
            )
    
    async def search_users(
        self,
        search_term: str,
        pagination: PaginationRequestDTO,
        include_inactive: bool = False
    ) -> PaginatedResponseDTO:
        """Search users"""
        try:
            return await self.user_use_cases.search_users(
                search_term=search_term,
                pagination=pagination,
                include_inactive=include_inactive
            )
        except Exception as e:
            print(f"Error searching users: {e}")
            return PaginatedResponseDTO.create([], 0, pagination)
    
    async def get_user_by_email(self, email: str) -> Optional[UserDTO]:
        """Get user by email (admin operation)"""
        try:
            return await self.user_use_cases.get_user_by_email(email)
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[UserDTO]:
        """Get user by username (admin operation)"""
        try:
            return await self.user_use_cases.get_user_by_username(username)
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None


class ApplicationServiceRegistry:
    """
    Registry for application services with dependency injection.
    
    Manages service instances and their dependencies.
    """
    
    def __init__(self):
        self._auth_service: Optional[AuthenticationService] = None
        self._user_service: Optional[UserService] = None
    
    def register_auth_service(self, auth_use_cases: AuthenticationUseCases) -> AuthenticationService:
        """Register authentication service"""
        self._auth_service = AuthenticationService(auth_use_cases)
        return self._auth_service
    
    def register_user_service(self, user_use_cases: UserManagementUseCases) -> UserService:
        """Register user service"""
        self._user_service = UserService(user_use_cases)
        return self._user_service
    
    @property
    def auth_service(self) -> AuthenticationService:
        """Get authentication service"""
        if not self._auth_service:
            raise RuntimeError("Authentication service not registered")
        return self._auth_service
    
    @property
    def user_service(self) -> UserService:
        """Get user service"""
        if not self._user_service:
            raise RuntimeError("User service not registered")
        return self._user_service


# Global service registry
_service_registry = ApplicationServiceRegistry()


def get_service_registry() -> ApplicationServiceRegistry:
    """Get the global service registry"""
    return _service_registry