"""
Authentication Schemas

Pydantic models for authentication API requests and responses.
These are used for API serialization/deserialization.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime

from ....application.dto import UserDTO
from ....domain.value_objects.role import UserRole


class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str = Field(..., description="Refresh token")


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr = Field(..., description="User's email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class EmailVerificationRequest(BaseModel):
    """Email verification request"""
    token: str = Field(..., description="Email verification token")


class AuthResponse(BaseModel):
    """Authentication response with user and tokens"""
    user: UserDTO = Field(..., description="User information")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    message: str = Field(..., description="Response message")


class RefreshTokenResponse(BaseModel):
    """Refresh token response"""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Success indicator")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class UserProfile(BaseModel):
    """User profile information"""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="Email address")
    role: UserRole = Field(..., description="User role")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    username: Optional[str] = Field(None, description="Username")
    is_verified: bool = Field(..., description="Email verification status")
    is_active: bool = Field(..., description="Account active status")
    created_at: datetime = Field(..., description="Account creation date")
    updated_at: Optional[datetime] = Field(None, description="Last update date")
    
    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    """Update user profile request"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Last name")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    error: str = Field(default="VALIDATION_ERROR", description="Error type")
    message: str = Field(..., description="Validation error message")
    field_errors: Optional[Dict[str, str]] = Field(None, description="Field-specific errors")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class EmailValidationResponse(BaseModel):
    """Email validation response"""
    is_valid: bool = Field(..., description="Whether the email is valid")
    message: str = Field(..., description="Validation message")
    suggestion: Optional[str] = Field(None, description="Email suggestion if invalid")
    reason: Optional[str] = Field(None, description="Reason if invalid")


class PasswordValidationResponse(BaseModel):
    """Password validation response"""
    is_valid: bool = Field(..., description="Whether the password is valid")
    strength_score: int = Field(..., description="Password strength score (0-4)")
    strength_level: str = Field(..., description="Password strength level")
    requirements: List[str] = Field(default_factory=list, description="Met requirements")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    estimated_crack_time: str = Field(default="", description="Estimated time to crack")