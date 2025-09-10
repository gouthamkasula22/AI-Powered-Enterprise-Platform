"""
User Model - Production Ready Authentication Model

Complete User model with all authentication fields and relationships.
This is a clean, production-ready implementation.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    String, Text, Boolean, Integer, DateTime, 
    CheckConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel

# Import for type checking only to avoid circular imports
if TYPE_CHECKING:
    from .session import UserSession
    from .social_account import SocialAccount
    from .otp import OTPVerification
    from .audit import LoginHistory
    from .password_history import PasswordHistory


class User(BaseModel):
    """
    Production-ready User model for authentication and user management.
    
    This model stores core user information including authentication credentials,
    profile information, security settings, and account management data.
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
        doc="Whether the user has superuser privileges"
    )
    
    # Security and login tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of last successful login"
    )
    
    last_login_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        doc="IP address of last login"
    )
    
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of consecutive failed login attempts"
    )
    
    account_locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp until which the account is locked"
    )
    
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when password was last changed"
    )
    
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
    
    # Activity tracking
    last_activity: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of last activity"
    )
    
    login_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total number of logins"
    )
    
    # Privacy and preferences
    email_notifications: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether to send email notifications"
    )
    
    marketing_emails: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether to send marketing emails"
    )
    
    # Relationships
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    login_history: Mapped[List["LoginHistory"]] = relationship(
        "LoginHistory",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    password_history: Mapped[List["PasswordHistory"]] = relationship(
        "PasswordHistory",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    social_accounts: Mapped[List["SocialAccount"]] = relationship(
        "SocialAccount",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    otp_verifications: Mapped[List["OTPVerification"]] = relationship(
        "OTPVerification",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Database constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "email ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'",
            name="email_format_check"
        ),
        CheckConstraint(
            "username ~ '^[a-zA-Z0-9_-]{3,50}$'",
            name="username_format_check"
        ),
        CheckConstraint(
            "failed_login_attempts >= 0",
            name="failed_login_attempts_positive"
        ),
        CheckConstraint(
            "login_count >= 0",
            name="login_count_positive"
        ),
        Index("ix_users_email_verified", "email", "is_verified"),
        Index("ix_users_active_verified", "is_active", "is_verified"),
        Index("ix_users_last_login", "last_login"),
        Index("ix_users_last_activity", "last_activity"),
    )
    
    # Properties
    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.display_name or self.username or self.email.split('@')[0]
    
    @property
    def is_account_locked(self) -> bool:
        """Check if the account is currently locked."""
        if self.account_locked_until:
            return datetime.utcnow() < self.account_locked_until
        return False
    
    @property
    def age(self) -> Optional[int]:
        """Calculate the user's age from date of birth."""
        if self.date_of_birth:
            today = datetime.utcnow().date()
            born = self.date_of_birth.date()
            return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        return None
    
    @property
    def initials(self) -> str:
        """Get the user's initials."""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.first_name:
            return self.first_name[0].upper()
        elif self.display_name:
            return self.display_name[0].upper()
        else:
            return self.email[0].upper()
    
    # Methods
    def can_login(self) -> bool:
        """Check if the user can login."""
        return (
            self.is_active and 
            not self.is_account_locked and
            self.password_hash is not None
        )
    
    def lock_account(self, duration_minutes: int = 30) -> None:
        """Lock the account for a specified duration."""
        self.account_locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
    
    def unlock_account(self) -> None:
        """Unlock the account."""
        self.account_locked_until = None
        self.failed_login_attempts = 0
    
    def increment_failed_login(self) -> None:
        """Increment failed login attempts."""
        self.failed_login_attempts += 1
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.lock_account(30)  # Lock for 30 minutes
    
    def reset_failed_login(self) -> None:
        """Reset failed login attempts."""
        self.failed_login_attempts = 0
    
    def update_last_login(self) -> None:
        """Update last login timestamp and increment login count."""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        self.reset_failed_login()
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_username(self, username: str) -> bool:
        """Validate username format."""
        pattern = r'^[a-zA-Z0-9_-]{3,50}$'
        return re.match(pattern, username) is not None
    
    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User(id={self.id}, email='{self.email}', is_active={self.is_active})>"
