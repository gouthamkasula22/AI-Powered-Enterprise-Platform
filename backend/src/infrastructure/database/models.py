"""
Database Models

SQLAlchemy models that map to existing database tables.
These models match the existing database schema to preserve data.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from .config import BaseModel


class UserModel(BaseModel):
    """
    SQLAlchemy model for the users table.
    
    This model maps to the existing users table in the database,
    preserving the current schema and data.
    """
    __tablename__ = 'users'
    
    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="User's email address (used for login)"
    )
    
    username: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        index=True,
        doc="Optional username (alternative login method)"
    )
    
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Hashed password (null for social-only accounts)"
    )
    
    auth_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default='PASSWORD',
        doc="Authentication method (password, google_oauth, github_oauth, etc.)"
    )
    
    auth_provider_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Provider user ID for OAuth authentication"
    )
    
    # Profile information
    first_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="User's first name"
    )
    
    last_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="User's last name"
    )
    
    display_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="User's preferred display name"
    )
    
    profile_picture_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="URL to user's profile picture"
    )
    
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="User's biography or description"
    )
    
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="User's phone number"
    )
    
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="User's date of birth"
    )
    
    # Account status and verification
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Whether the account is active"
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether the email is verified"
    )
    
    email_verification_token: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        doc="Token for email verification"
    )
    
    email_verification_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the email verification token expires"
    )
    
    # Password Reset fields
    password_reset_token: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        doc="Token for password reset"
    )
    
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the password reset token expires"
    )
    
    # Security and metadata
    is_staff: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether the user is a staff member"
    )
    
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether the user is a superuser"
    )
    
    # Role-Based Access Control
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default='USER',
        index=True,
        doc="User's role for RBAC (USER, ADMIN, SUPERADMIN)"
    )
    
    failed_login_attempts: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        doc="Number of consecutive failed login attempts"
    )
    
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the account lock expires"
    )
    
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last successful login timestamp"
    )
    
    timezone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default='UTC',
        doc="User's preferred timezone"
    )
    
    locale: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        default='en',
        doc="User's preferred locale/language"
    )
    
    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Soft delete timestamp"
    )
    
    def __repr__(self) -> str:
        return f"<UserModel(id={self.id}, email='{self.email}', active={self.is_active})>"