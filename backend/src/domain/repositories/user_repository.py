"""
User Repository Interface

Abstract interface defining data access operations for Users.
Infrastructure layer will implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from ..entities.user import User
from ..value_objects.email import Email


class IUserRepository(ABC):
    """
    User repository interface defining data access contract.
    
    This interface follows the Repository pattern and defines all
    data access operations without implementation details.
    """
    
    @abstractmethod
    async def find_by_id(self, user_id: int) -> Optional[User]:
        """
        Find user by ID
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            User entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_by_email(self, email: Email) -> Optional[User]:
        """
        Find user by email address
        
        Args:
            email: User's email address
            
        Returns:
            User entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        """
        Find user by username
        
        Args:
            username: User's username
            
        Returns:
            User entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_by_verification_token(self, token: str) -> Optional[User]:
        """
        Find user by email verification token
        
        Args:
            token: Email verification token
            
        Returns:
            User entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_by_email_verification_token(self, token: str) -> Optional[User]:
        """
        Find user by email verification token (alias for compatibility)
        
        Args:
            token: Email verification token
            
        Returns:
            User entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find_by_password_reset_token(self, token: str) -> Optional[User]:
        """
        Find user by password reset token
        
        Args:
            token: Password reset token
            
        Returns:
            User entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """
        Create a new user
        
        Args:
            user: User entity to create
            
        Returns:
            Created user entity with assigned ID
            
        Raises:
            EmailAlreadyExistsException: If email is already registered
        """
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """
        Update existing user
        
        Args:
            user: User entity to update
            
        Returns:
            Updated user entity
            
        Raises:
            UserNotFoundException: If user doesn't exist
        """
        pass
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """
        Save user (create or update)
        
        Args:
            user: User entity to save
            
        Returns:
            Saved user entity
        """
        pass
    
    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """
        Delete user by ID
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: Email) -> bool:
        """
        Check if user exists with given email
        
        Args:
            email: Email address to check
            
        Returns:
            True if user exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def find_active_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        Find active users with pagination
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of active user entities
        """
        pass
    
    @abstractmethod
    async def find_unverified_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        Find unverified users with pagination
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of unverified user entities
        """
        pass
    
    @abstractmethod
    async def list_users(self, limit: int = 100, offset: int = 0, 
                        include_inactive: bool = False) -> List[User]:
        """
        List users with pagination and filtering
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            include_inactive: Whether to include inactive users
            
        Returns:
            List of user entities
        """
        pass
    
    @abstractmethod
    async def count_total_users(self) -> int:
        """
        Count total number of users
        
        Returns:
            Total number of users in system
        """
        pass
    
    @abstractmethod
    async def count_active_users(self) -> int:
        """
        Count active users
        
        Returns:
            Number of active users
        """
        pass