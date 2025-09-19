"""
User Management Use Cases

Business workflows for user profile management, account administration,
and user data operations.
"""

from typing import List, Optional
from datetime import datetime

from ..dto import (
    UserDTO, UpdateProfileRequestDTO, PaginationRequestDTO,
    PaginatedResponseDTO, MessageResponseDTO, user_entity_to_dto,
    UpdateUserProfileRequestDTO, UserListQueryDTO, UserListResponseDTO
)
from ..commands import (
    UpdateProfileCommand, UpdateProfilePictureCommand,
    DeactivateAccountCommand, ReactivateAccountCommand
)
from ..queries import (
    GetUserByIdQuery, GetUserProfileQuery, ListUsersQuery,
    SearchUsersQuery
)
from ...domain.entities.user import User
from ...domain.repositories.user_repository import IUserRepository
from ...domain.exceptions import (
    UserNotFoundException, AccountDeactivatedException,
    ValidationError
)


class UserManagementUseCases:
    """
    User management use cases for profile and account operations.
    
    Handles user profile updates, account management, and user search/listing.
    """
    
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
    
    async def get_user_profile(self, user_id: int) -> UserDTO:
        """
        Get user profile information.
        
        Business rules:
        - User must exist
        - Return complete profile data
        """
        
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))
        
        return user_entity_to_dto(user)
    
    async def update_profile_picture(
        self, 
        user_id: int, 
        profile_picture_url: str
    ) -> UserDTO:
        """
        Update user profile picture.
        
        Business rules:
        - User must exist and be active
        - Validate URL format
        """
        
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))
        
        if not user.is_active:
            raise AccountDeactivatedException()
        
        # Basic URL validation
        if not profile_picture_url.startswith(('http://', 'https://')):
            raise ValidationError("Profile picture must be a valid URL")
        
        user.profile_picture_url = profile_picture_url
        user.update_profile()
        updated_user = await self.user_repository.save(user)
        
        return user_entity_to_dto(updated_user)
    
    async def deactivate_account(self, user_id: int) -> MessageResponseDTO:
        """
        Deactivate user account.
        
        Business rules:
        - User must exist
        - Account becomes inactive
        - Sessions remain valid until expiration
        """
        
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))
        
        user.deactivate_account()
        await self.user_repository.save(user)
        
        return MessageResponseDTO(
            message="Account deactivated successfully",
            success=True
        )
    
    async def reactivate_account(self, user_id: int) -> MessageResponseDTO:
        """
        Reactivate user account.
        
        Business rules:
        - User must exist
        - Account becomes active again
        """
        
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))
        
        user.reactivate_account()
        await self.user_repository.save(user)
        
        return MessageResponseDTO(
            message="Account reactivated successfully",
            success=True
        )
    
    async def search_users(
        self,
        search_term: str,
        pagination: PaginationRequestDTO,
        include_inactive: bool = False
    ) -> PaginatedResponseDTO:
        """
        Search users by name, email, or username.
        
        Business rules:
        - Search across multiple fields
        - Support pagination
        - Optionally include inactive users
        """
        
        # Get all users (simplified - in production would be optimized)
        users = await self.user_repository.list_users(offset=0, limit=1000)
        
        # Filter by search term
        search_lower = search_term.lower()
        matching_users = []
        
        for user in users:
            if not include_inactive and not user.is_active:
                continue
            
            if any([
                search_lower in (user.email.value if user.email else "").lower(),
                search_lower in (user.first_name or "").lower(),
                search_lower in (user.last_name or "").lower(),
                search_lower in (user.username or "").lower(),
                search_lower in (user.display_name or "").lower()
            ]):
                matching_users.append(user)
        
        # Apply pagination
        start_idx = pagination.skip
        end_idx = start_idx + pagination.limit
        paginated_users = matching_users[start_idx:end_idx]
        
        # Convert to DTOs
        user_dtos = [user_entity_to_dto(user) for user in paginated_users]
        
        return PaginatedResponseDTO.create(
            items=user_dtos,
            total=len(matching_users),
            pagination=pagination
        )
    
    async def get_user_by_email(self, email: str) -> Optional[UserDTO]:
        """
        Get user by email address.
        
        Business rules:
        - Return user if exists, None otherwise
        - Used for admin operations
        """
        
        from ...domain.value_objects.email import Email
        email_vo = Email(email)
        user = await self.user_repository.find_by_email(email_vo)
        
        return user_entity_to_dto(user) if user else None
    
    async def get_user_by_username(self, username: str) -> Optional[UserDTO]:
        """
        Get user by username.
        
        Business rules:
        - Return user if exists, None otherwise
        - Used for admin operations
        """
        
        user = await self.user_repository.find_by_username(username)
        return user_entity_to_dto(user) if user else None
    
    async def update_user_profile(self, request: "UpdateUserProfileRequestDTO") -> UserDTO:
        """
        Update user profile information
        
        Args:
            request: Update profile request
            
        Returns:
            Updated user information
            
        Raises:
            UserNotFoundException: If user not found
            ValidationError: If update data is invalid
        """
        user = await self.user_repository.find_by_id(request.user_id)
        if not user:
            raise UserNotFoundException("User not found")
        
        # Update fields if provided
        if request.first_name is not None:
            user.first_name = request.first_name
        if request.last_name is not None:
            user.last_name = request.last_name
        if request.username is not None:
            user.username = request.username
        if request.display_name is not None:
            user.display_name = request.display_name
        if request.bio is not None:
            user.bio = request.bio
        if request.phone_number is not None:
            user.phone_number = request.phone_number
        
        user.updated_at = datetime.utcnow()
        await self.user_repository.update(user)
        
        return user_entity_to_dto(user)
    
    async def get_user_by_id(self, user_id: str) -> UserDTO:
        """Get user by ID (for admin operations)"""
        user = await self.user_repository.find_by_id(int(user_id))
        if not user:
            raise UserNotFoundException("User not found")
        return user_entity_to_dto(user)
    
    async def delete_user(self, user_id: int) -> MessageResponseDTO:
        """Delete user account"""
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException("User not found")
        
        await self.user_repository.delete(user_id)
        return MessageResponseDTO(message="User account deleted successfully")
    
    async def activate_user(self, user_id: str) -> MessageResponseDTO:
        """Activate user account (admin only)"""
        user = await self.user_repository.find_by_id(int(user_id))
        if not user:
            raise UserNotFoundException("User not found")
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        await self.user_repository.update(user)
        
        return MessageResponseDTO(message="User account activated successfully")
    
    async def deactivate_user(self, user_id: str) -> MessageResponseDTO:
        """Deactivate user account (admin only)"""
        user = await self.user_repository.find_by_id(int(user_id))
        if not user:
            raise UserNotFoundException("User not found")
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        await self.user_repository.update(user)
        
        return MessageResponseDTO(message="User account deactivated successfully")
    
    async def list_users(self, query: "UserListQueryDTO") -> "UserListResponseDTO":
        """List users with pagination and filtering (admin only)"""
        # For now, return empty list - will implement with actual database
        from ..dto import UserListResponseDTO
        return UserListResponseDTO(
            users=[],
            total=0,
            page=query.page,
            limit=query.limit,
            pages=0
        )