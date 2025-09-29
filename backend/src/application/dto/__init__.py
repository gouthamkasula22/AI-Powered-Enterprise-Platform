"""
Data Transfer Objects (DTOs)

DTOs define the data structures for application layer boundaries.
They ensure clean data contracts between layers and API endpoints.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator

from ...domain.value_objects.role import UserRole


# Base DTOs
class BaseDTO(BaseModel):
    """Base DTO with common validation"""
    class Config:
        validate_assignment = True
        str_strip_whitespace = True


# Authentication DTOs
@dataclass
class UserDTO:
    """User data transfer object for application responses"""
    id: int
    email: str
    created_at: datetime
    updated_at: datetime
    role: UserRole = UserRole.USER
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    is_active: bool = True
    is_verified: bool = False
    is_staff: bool = False
    is_superuser: bool = False
    is_admin: bool = False  # Add missing is_admin field
    permissions: Optional[List[str]] = None  # Add missing permissions field
    timezone: str = "UTC"
    locale: str = "en"
    last_login: Optional[datetime] = None


class RegisterRequestDTO(BaseDTO):
    """Request DTO for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password meets minimum requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class LoginRequestDTO(BaseDTO):
    """Request DTO for user login"""
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)
    remember_me: bool = False


@dataclass
class LoginResponseDTO:
    """Response DTO for successful login"""
    user: UserDTO
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds


class RefreshTokenRequestDTO(BaseDTO):
    """Request DTO for token refresh"""
    refresh_token: str = Field(..., min_length=10)


@dataclass
class RefreshTokenResponseDTO:
    """Response DTO for token refresh"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800


class PasswordResetRequestDTO(BaseDTO):
    """Request DTO for password reset initiation"""
    email: EmailStr


class PasswordResetConfirmDTO(BaseDTO):
    """Request DTO for password reset confirmation"""
    token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password meets minimum requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class ChangePasswordRequestDTO(BaseDTO):
    """Request DTO for password change"""
    user_id: int = Field(..., description="User ID")
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password meets minimum requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class EmailVerificationRequestDTO(BaseDTO):
    """Request DTO for email verification"""
    token: str = Field(..., min_length=10)


# Profile Management DTOs
class UpdateProfileRequestDTO(BaseDTO):
    """Request DTO for profile updates"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    phone_number: Optional[str] = Field(None, max_length=20)
    timezone: Optional[str] = Field(None, max_length=50)
    locale: Optional[str] = Field(None, max_length=10)


# Response DTOs
@dataclass
class MessageResponseDTO:
    """Generic message response"""
    message: str
    success: bool = True


@dataclass
class ErrorResponseDTO:
    """Error response DTO"""
    error: str
    error_code: str
    details: Optional[dict] = None
    success: bool = False


@dataclass
class ValidationErrorResponseDTO:
    """Validation error response DTO"""
    validation_errors: List[dict]
    error: str = "Validation failed"
    error_code: str = "VALIDATION_ERROR"
    success: bool = False


# Pagination DTOs
class PaginationRequestDTO(BaseDTO):
    """Request DTO for pagination"""
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=100)
    
    @property
    def skip(self) -> int:
        """Calculate skip value for database queries"""
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        """Get limit value for database queries"""
        return self.size


@dataclass
class PaginatedResponseDTO:
    """Paginated response DTO"""
    items: List
    total: int
    page: int
    size: int
    pages: int
    
    @classmethod
    def create(cls, items: List, total: int, pagination: PaginationRequestDTO):
        """Create paginated response from items and pagination request"""
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=((total - 1) // pagination.size) + 1 if total > 0 else 0
        )


# Utility functions for DTO conversion
def user_entity_to_dto(user) -> UserDTO:
    """Convert User entity to UserDTO"""
    # Handle role conversion more robustly
    user_role = user.role if user.role else UserRole.USER
    
    # Ensure role is a UserRole enum instance
    if isinstance(user_role, str):
        try:
            # Convert string role to UserRole enum (handles both uppercase and lowercase)
            role_value = user_role.lower()
            user_role = UserRole(role_value)
        except ValueError:
            user_role = UserRole.USER
    
    # Calculate admin status based on role (handle both string and enum)
    is_admin_role = False
    if user_role:
        if isinstance(user_role, UserRole):
            is_admin_role = user_role in [UserRole.ADMIN, UserRole.SUPERADMIN]
        else:
            # Handle string role (could be uppercase or lowercase)
            role_str = str(user_role).lower()
            is_admin_role = role_str in ['admin', 'superadmin']
    
    return UserDTO(
        id=user.id,
        email=user.email.value if user.email else "",
        created_at=user.created_at,
        updated_at=user.updated_at,
        role=user_role,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=user.display_name,
        profile_picture_url=user.profile_picture_url,
        bio=user.bio,
        phone_number=user.phone_number,
        date_of_birth=user.date_of_birth,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_staff=user.is_staff,
        is_superuser=user.is_superuser,
        is_admin=is_admin_role or user.is_superuser,  # Include superuser flag as fallback
        timezone=user.timezone,
        locale=user.locale,
        last_login=user.last_login
    )


# Missing DTOs for User Management
class UpdateUserProfileRequestDTO(BaseDTO):
    """Request DTO for updating user profile"""
    user_id: int = Field(..., description="User ID")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    username: Optional[str] = Field(None, max_length=50)
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    phone_number: Optional[str] = Field(None, max_length=20)


class UserListQueryDTO(BaseDTO):
    """Query DTO for listing users"""
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Items per page")
    search: Optional[str] = Field(None, description="Search by email or name")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_verified: Optional[bool] = Field(None, description="Filter by verification status")


class UserListResponseDTO(BaseDTO):
    """Response DTO for user list"""
    users: List[UserDTO] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page")
    limit: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total pages")