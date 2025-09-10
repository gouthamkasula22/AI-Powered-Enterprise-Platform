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
    created_at: datetime = Field(..., description="Account creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    """Complete authentication response schema"""
    message: str = Field(..., description="Response message")
    user: UserResponse = Field(..., description="User information")
    tokens: TokenResponse = Field(..., description="JWT tokens")


class PasswordValidationResponse(BaseModel):
    """Password validation response schema"""
    valid: bool = Field(..., description="Whether password is valid")
    errors: List[str] = Field(default_factory=list, description="Validation error messages")
    strength_score: int = Field(..., description="Password strength score (0-100)")
    requirements: Dict[str, bool] = Field(..., description="Password requirement compliance")


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
