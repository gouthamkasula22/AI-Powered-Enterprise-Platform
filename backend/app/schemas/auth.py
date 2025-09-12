"""
Authentication Schemas

Pydantic models for authentication API requests and responses.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegisterRequest(BaseModel):
    """User registration request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")


class UserLoginRequest(BaseModel):
    """User login request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class PasswordChangeRequest(BaseModel):
    """Password change request schema"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")


class ForgotPasswordRequest(BaseModel):
    """Forgot password request schema"""
    email: EmailStr = Field(..., description="User email address")


class ResetPasswordRequest(BaseModel):
    """Reset password request schema"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="JWT refresh token")


class EmailVerificationRequest(BaseModel):
    """Email verification request schema"""
    token: str = Field(..., description="Email verification token")


class ProfileUpdateRequest(BaseModel):
    """Profile update request schema"""
    first_name: Optional[str] = Field(None, max_length=50, description="User first name")
    last_name: Optional[str] = Field(None, max_length=50, description="User last name")
    display_name: Optional[str] = Field(None, max_length=100, description="User display name")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    phone_number: Optional[str] = Field(None, max_length=20, description="User phone number")
    date_of_birth: Optional[datetime] = Field(None, description="User date of birth")


class EmailValidationRequest(BaseModel):
    """Email validation request schema"""
    email: EmailStr = Field(..., description="Email address to validate")


class EmailValidationResponse(BaseModel):
    """Email validation response schema"""
    is_valid: bool = Field(..., description="Whether the email is valid")
    reason: Optional[str] = Field(None, description="Reason if email is invalid")
    suggestion: Optional[str] = Field(None, description="Suggested correction for typos")
    domain: Optional[str] = Field(None, description="Email domain")
    normalized_email: Optional[str] = Field(None, description="Normalized email address")


class PasswordRequirementCheck(BaseModel):
    """Individual password requirement check result"""
    name: str = Field(..., description="Requirement name")
    description: str = Field(..., description="Human-readable requirement description")
    is_met: bool = Field(..., description="Whether this requirement is satisfied")


class PasswordValidationRequest(BaseModel):
    """Password validation request schema"""
    password: str = Field(..., description="Password to validate")
    email: Optional[str] = Field(None, description="User email for personalized validation")


class ResendVerificationRequest(BaseModel):
    """Resend verification email request schema"""
    email: EmailStr = Field(..., description="User email address")


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")  
    token_type: str = Field(default="bearer", description="Token type")


class UserResponse(BaseModel):
    """User information response schema"""
    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email address")
    is_verified: bool = Field(..., description="Whether the email is verified")
    is_active: bool = Field(..., description="Whether the account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")
    display_name: Optional[str] = Field(None, description="User display name")
    bio: Optional[str] = Field(None, description="User bio")
    phone_number: Optional[str] = Field(None, description="User phone number")
    date_of_birth: Optional[datetime] = Field(None, description="User date of birth")
    profile_picture_url: Optional[str] = Field(None, description="User profile picture URL")
    
    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    """Complete authentication response schema"""
    message: str = Field(..., description="Response message")
    user: UserResponse = Field(..., description="User information")
    tokens: TokenResponse = Field(..., description="JWT tokens")


class PasswordValidationResponse(BaseModel):
    """Password validation response schema"""
    is_valid: bool = Field(..., description="Whether the password meets all requirements")
    strength_score: int = Field(..., description="Password strength score (0-100)")
    strength_level: str = Field(..., description="Strength level (Weak, Fair, Good, Strong, Very Strong)")
    requirements: List[PasswordRequirementCheck] = Field(..., description="Individual requirement checks")
    suggestions: List[str] = Field(..., description="Suggestions for improvement")
    estimated_crack_time: str = Field(..., description="Estimated time to crack this password")


class LogoutResponse(BaseModel):
    """Logout response schema"""
    message: str = Field(..., description="Logout confirmation message")


class UserInfoResponse(BaseModel):
    """Current user info response schema"""
    user: UserResponse = Field(..., description="Current user information")


class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str = Field(..., description="Error message")
    errors: Optional[List[str]] = Field(None, description="Additional error details")


class SuccessResponse(BaseModel):
    """Generic success response schema"""
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")


class EmailVerificationResponse(BaseModel):
    """Email verification response schema"""
    message: str = Field(..., description="Verification result message")
    user: UserResponse = Field(..., description="User information")


class MessageResponse(BaseModel):
    """Simple message response schema"""
    message: str = Field(..., description="Response message")


class ResetPasswordResponse(BaseModel):
    """Password reset response schema"""
    message: str = Field(..., description="Reset confirmation message")
    user: UserResponse = Field(..., description="User information")


class ValidateResetTokenRequest(BaseModel):
    """Validate reset token request schema"""
    token: str = Field(..., description="Password reset token to validate")


class ValidateResetTokenResponse(BaseModel):
    """Validate reset token response schema"""
    is_valid: bool = Field(..., description="Whether the token is valid")
    message: str = Field(..., description="Status message")
    email: Optional[str] = Field(None, description="Email associated with valid token")
