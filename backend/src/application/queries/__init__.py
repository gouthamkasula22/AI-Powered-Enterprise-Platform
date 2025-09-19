"""
Queries - Read Operations

Queries represent read operations that don't change system state.
They follow the Query pattern and return specific data views.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Query:
    """Base query class"""
    pass


# User Queries
@dataclass
class GetUserByIdQuery(Query):
    """Query to get user by ID"""
    user_id: int


@dataclass
class GetUserByEmailQuery(Query):
    """Query to get user by email"""
    email: str


@dataclass
class GetUserByUsernameQuery(Query):
    """Query to get user by username"""
    username: str


@dataclass
class GetUserByVerificationTokenQuery(Query):
    """Query to get user by email verification token"""
    token: str


@dataclass
class GetUserByPasswordResetTokenQuery(Query):
    """Query to get user by password reset token"""
    token: str


@dataclass
class ListUsersQuery(Query):
    """Query to list users with pagination"""
    page: int = 1
    size: int = 50
    search: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


# Profile Queries
@dataclass
class GetUserProfileQuery(Query):
    """Query to get user profile information"""
    user_id: int


@dataclass
class SearchUsersQuery(Query):
    """Query to search users by various criteria"""
    search_term: str
    page: int = 1
    size: int = 20
    include_inactive: bool = False


# Authentication Queries
@dataclass
class ValidateTokenQuery(Query):
    """Query to validate authentication token"""
    token: str
    token_type: str


@dataclass
class GetUserSessionsQuery(Query):
    """Query to get user's active sessions"""
    user_id: int