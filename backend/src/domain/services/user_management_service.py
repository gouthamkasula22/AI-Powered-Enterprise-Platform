"""
User Management Domain Service

Business logic for user profile management and account operations.
"""

from datetime import datetime
from typing import Optional
from ..entities.user import User
from ..value_objects.email import Email
from ..repositories.user_repository import IUserRepository
from ..exceptions.domain_exceptions import (
    UserNotFoundException,
    EmailAlreadyExistsException,
    AccountDeactivatedException,
    ValidationError
)


class UserManagementService:
    """
    Domain service for user management operations.
    
    Handles complex business logic around user profile management,
    account operations, and administrative functions.
    """
    
    def __init__(self, user_repository: IUserRepository):
        self._user_repository = user_repository
    
    async def update_user_profile(
        self,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        display_name: Optional[str] = None,
        bio: Optional[str] = None,
        phone_number: Optional[str] = None,
        date_of_birth: Optional[datetime] = None
    ) -> User:
        """
        Update user profile information
        
        Args:
            user_id: User's ID
            first_name: Updated first name
            last_name: Updated last name
            display_name: Updated display name
            bio: Updated biography
            phone_number: Updated phone number
            date_of_birth: Updated date of birth
            
        Returns:
            Updated user entity
            
        Raises:
            UserNotFoundException: If user not found
            AccountDeactivatedException: If account is deactivated
            ValidationError: If validation fails
        """
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))
        
        # Update profile using entity business logic
        user.update_profile(
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
            bio=bio,
            phone_number=phone_number,
            date_of_birth=date_of_birth
        )
        
        return await self._user_repository.update(user)
    
    async def change_user_email(self, user_id: int, new_email: Email) -> User:
        """
        Change user's email address
        
        Args:
            user_id: User's ID
            new_email: New email address
            
        Returns:
            Updated user entity
            
        Raises:
            UserNotFoundException: If user not found
            EmailAlreadyExistsException: If new email is already taken
            AccountDeactivatedException: If account is deactivated
        """
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))
        
        # Business rule: Email must be unique
        if await self._user_repository.exists_by_email(new_email):
            raise EmailAlreadyExistsException(new_email.value)
        
        # Change email (requires re-verification)
        user._ensure_account_active()
        user.email = new_email
        user.is_verified = False  # Require re-verification for new email
        user.email_verification_token = None
        user.email_verification_expires = None
        user.updated_at = datetime.utcnow()
        
        return await self._user_repository.update(user)
    
    async def deactivate_user_account(self, user_id: int) -> User:
        """
        Deactivate user account
        
        Args:
            user_id: User's ID
            
        Returns:
            Updated user entity
            
        Raises:
            UserNotFoundException: If user not found
        """
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))
        
        user.deactivate_account()
        return await self._user_repository.update(user)
    
    async def reactivate_user_account(self, user_id: int) -> User:
        """
        Reactivate user account
        
        Args:
            user_id: User's ID
            
        Returns:
            Updated user entity
            
        Raises:
            UserNotFoundException: If user not found
        """
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))
        
        user.reactivate_account()
        return await self._user_repository.update(user)
    
    async def delete_user_account(self, user_id: int) -> bool:
        """
        Permanently delete user account
        
        Args:
            user_id: User's ID
            
        Returns:
            True if deleted, False if not found
            
        Note:
            This is a permanent operation. Consider deactivation instead
            for compliance with data retention policies.
        """
        return await self._user_repository.delete(user_id)
    
    async def make_user_staff(self, user_id: int) -> User:
        """
        Grant staff privileges to user
        
        Args:
            user_id: User's ID
            
        Returns:
            Updated user entity
            
        Raises:
            UserNotFoundException: If user not found
            AccountDeactivatedException: If account is deactivated
        """
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))
        
        user.make_staff()
        return await self._user_repository.update(user)
    
    async def remove_user_staff(self, user_id: int) -> User:
        """
        Remove staff privileges from user
        
        Args:
            user_id: User's ID
            
        Returns:
            Updated user entity
            
        Raises:
            UserNotFoundException: If user not found
        """
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))
        
        user.remove_staff()
        return await self._user_repository.update(user)