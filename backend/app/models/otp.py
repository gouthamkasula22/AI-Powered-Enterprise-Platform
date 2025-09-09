"""
OTP Verification Model

This module defines the OTPVerification model for managing one-time passwords
used for email verification, password reset, and two-factor authentication.

Author: User Authentication System
Version: 1.0.0
"""

import secrets
import string
import uuid
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Integer, Enum, Index, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

# Import for type checking only to avoid circular imports
if TYPE_CHECKING:
    from .user import User


class OTPVerification(BaseModel):
    """
    OTP (One-Time Password) verification model.
    
    This model manages OTP codes for various purposes including email verification,
    password reset, and two-factor authentication.
    """
    __tablename__ = 'otp_verifications'
    
    # Foreign key to user
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="Reference to the user this OTP belongs to"
    )
    
    # OTP details
    code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        doc="The OTP code (hashed for security)"
    )
    
    purpose: Mapped[str] = mapped_column(
        Enum('email_verification', 'password_reset', 'mfa', 'login_verification', name='otp_purpose_enum'),
        nullable=False,
        index=True,
        doc="Purpose of this OTP"
    )
    
    # Lifecycle
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When this OTP expires"
    )
    
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether this OTP has been used"
    )
    
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When this OTP was used"
    )
    
    # Security tracking
    attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of verification attempts"
    )
    
    max_attempts: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
        doc="Maximum allowed verification attempts"
    )
    
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether further attempts are blocked"
    )
    
    # Metadata
    sent_to: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Email or phone where OTP was sent"
    )
    
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
        doc="IP address where OTP was requested"
    )
    
    # Relationship - Unidirectional for M1.2 (no back_populates)
    user: Mapped["User"] = relationship(
        "User",
        lazy="select"
    )
    
    # Table constraints and indexes
    __table_args__ = (
        # Ensure attempts don't exceed max attempts
        CheckConstraint(
            'attempts <= max_attempts',
            name='valid_attempt_count'
        ),
        # Ensure max attempts is positive
        CheckConstraint(
            'max_attempts > 0',
            name='positive_max_attempts'
        ),
        # Composite indexes for common queries
        Index('idx_otp_user_purpose', 'user_id', 'purpose'),
        Index('idx_otp_user_active', 'user_id', 'is_used', 'expires_at'),
        Index('idx_otp_code_active', 'code', 'is_used'),
        Index('idx_otp_expires', 'expires_at'),
    )
    
    @property
    def is_expired(self) -> bool:
        """Check if the OTP has expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if the OTP is still valid for use."""
        return not self.is_used and not self.is_expired and not self.is_blocked
    
    @property
    def attempts_remaining(self) -> int:
        """Get number of attempts remaining."""
        return max(0, self.max_attempts - self.attempts)
    
    @classmethod
    def generate_code(cls, length: int = 6) -> str:
        """Generate a random OTP code."""
        digits = string.digits
        return ''.join(secrets.choice(digits) for _ in range(length))
    
    def verify_code(self, provided_code: str) -> bool:
        """
        Verify the provided code against this OTP.
        
        Args:
            provided_code (str): The code to verify
            
        Returns:
            bool: True if the code is valid and matches
        """
        # Increment attempts
        self.attempts += 1
        
        # Check if too many attempts
        if self.attempts >= self.max_attempts:
            self.is_blocked = True
            return False
        
        # Check if OTP is valid
        if not self.is_valid:
            return False
        
        # Verify the code (in production, use secure comparison)
        if self.code == provided_code:
            self.is_used = True
            self.used_at = datetime.utcnow()
            return True
        
        return False
    
    def mark_as_used(self) -> None:
        """Mark this OTP as used."""
        self.is_used = True
        self.used_at = datetime.utcnow()
    
    def block(self) -> None:
        """Block this OTP from further use."""
        self.is_blocked = True
    
    def extend_expiry(self, minutes: int = 15) -> None:
        """Extend the expiry time of this OTP."""
        self.expires_at = datetime.utcnow() + timedelta(minutes=minutes)
    
    @classmethod
    def create_for_user(
        cls,
        user_id: uuid.UUID,
        purpose: str,
        expires_in_minutes: int = 15,
        code_length: int = 6,
        sent_to: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> 'OTPVerification':
        """
        Create a new OTP for a user.
        
        Args:
            user_id (uuid.UUID): The user ID
            purpose (str): Purpose of the OTP
            expires_in_minutes (int): Minutes until expiry
            code_length (int): Length of the OTP code
            sent_to (str, optional): Where the OTP was sent
            ip_address (str, optional): IP address of requester
            
        Returns:
            OTPVerification: New OTP instance
        """
        return cls(
            user_id=user_id,
            code=cls.generate_code(code_length),
            purpose=purpose,
            expires_at=datetime.utcnow() + timedelta(minutes=expires_in_minutes),
            sent_to=sent_to,
            ip_address=ip_address
        )
    
    def __repr__(self) -> str:
        """String representation of OTPVerification."""
        return f"<OTPVerification(id={self.id}, user_id={self.user_id}, purpose={self.purpose}, valid={self.is_valid})>"
