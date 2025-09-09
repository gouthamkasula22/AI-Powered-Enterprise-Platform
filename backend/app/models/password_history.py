"""
Password History Model

This module defines the PasswordHistory model for tracking password changes,
preventing password reuse, and maintaining security compliance.

Author: User Authentication System
Version: 1.0.0
"""

import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Integer, Float, Text, Index, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

# Import for type checking only to avoid circular imports
if TYPE_CHECKING:
    from .user import User


class PasswordHistory(BaseModel):
    """
    Password history model for tracking password changes and preventing reuse.
    
    This model stores hashed passwords to prevent users from reusing recent passwords
    and tracks password strength metrics for security compliance.
    """
    __tablename__ = 'password_history'
    
    # Foreign key to user
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        doc="Reference to the user who owns this password"
    )
    
    # Password information
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Hashed password (for comparison only)"
    )
    
    # Security metrics
    strength_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Password strength score (0-1)"
    )
    
    entropy: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Password entropy in bits"
    )
    
    # Password characteristics
    length: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Length of the password"
    )
    
    has_uppercase: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether password contains uppercase letters"
    )
    
    has_lowercase: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether password contains lowercase letters"
    )
    
    has_digits: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether password contains digits"
    )
    
    has_symbols: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether password contains special symbols"
    )
    
    # Compliance and policy
    is_compromised: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Whether this password was found in breach databases"
    )
    
    compromise_source: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Source where password compromise was detected"
    )
    
    policy_compliant: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether password meets security policy requirements"
    )
    
    policy_violations: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON array of policy violations"
    )
    
    # Usage tracking
    set_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="When this password was set"
    )
    
    replaced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When this password was replaced"
    )
    
    last_used: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last time this password was used for login"
    )
    
    usage_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of times this password was used"
    )
    
    # Change metadata
    change_reason: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Reason for password change (expired, reset, voluntary, etc.)"
    )
    
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
        doc="IP address where password was changed"
    )
    
    # Relationship - Unidirectional for M1.2 (no back_populates)
    user: Mapped["User"] = relationship(
        "User",
        lazy="select"
    )
    
    # Table constraints and indexes
    __table_args__ = (
        # Ensure strength score is between 0 and 1
        CheckConstraint(
            'strength_score IS NULL OR (strength_score >= 0 AND strength_score <= 1)',
            name='valid_strength_score'
        ),
        # Ensure entropy is positive
        CheckConstraint(
            'entropy IS NULL OR entropy >= 0',
            name='positive_entropy'
        ),
        # Ensure length is positive
        CheckConstraint(
            'length > 0',
            name='positive_length'
        ),
        # Ensure usage count is non-negative
        CheckConstraint(
            'usage_count >= 0',
            name='non_negative_usage'
        ),
        # Composite indexes for common queries
        Index('idx_password_user_set', 'user_id', 'set_at'),
        Index('idx_password_user_active', 'user_id', 'replaced_at'),
        Index('idx_password_compromised', 'is_compromised', 'user_id'),
        Index('idx_password_compliance', 'policy_compliant', 'user_id'),
        Index('idx_password_strength', 'strength_score'),
    )
    
    @property
    def is_current(self) -> bool:
        """Check if this is the current password (not replaced)."""
        return self.replaced_at is None
    
    @property
    def age_days(self) -> int:
        """Get the age of this password in days."""
        age = datetime.utcnow() - self.set_at
        return age.days
    
    @property
    def strength_level(self) -> str:
        """Get a human-readable strength level."""
        if not self.strength_score:
            return "Unknown"
        
        if self.strength_score >= 0.8:
            return "Very Strong"
        elif self.strength_score >= 0.6:
            return "Strong"
        elif self.strength_score >= 0.4:
            return "Moderate"
        elif self.strength_score >= 0.2:
            return "Weak"
        else:
            return "Very Weak"
    
    def calculate_strength_score(self, password: str) -> float:
        """
        Calculate password strength score.
        
        Args:
            password (str): The plain text password
            
        Returns:
            float: Strength score between 0 and 1
        """
        score = 0.0
        
        # Length scoring
        if len(password) >= 12:
            score += 0.3
        elif len(password) >= 8:
            score += 0.2
        elif len(password) >= 6:
            score += 0.1
        
        # Character diversity
        if self.has_uppercase:
            score += 0.15
        if self.has_lowercase:
            score += 0.15
        if self.has_digits:
            score += 0.15
        if self.has_symbols:
            score += 0.25
        
        return min(1.0, score)
    
    def analyze_password(self, password: str) -> None:
        """
        Analyze password characteristics and update fields.
        
        Args:
            password (str): The plain text password
        """
        self.length = len(password)
        self.has_uppercase = any(c.isupper() for c in password)
        self.has_lowercase = any(c.islower() for c in password)
        self.has_digits = any(c.isdigit() for c in password)
        self.has_symbols = any(not c.isalnum() for c in password)
        
        # Calculate strength score
        self.strength_score = self.calculate_strength_score(password)
        
        # Calculate entropy (simplified)
        unique_chars = len(set(password))
        if unique_chars > 0:
            ratio = unique_chars / len(password)
            self.entropy = len(password) * int(ratio * 8)  # Simplified entropy calculation
    
    def mark_compromised(self, source: str | None = None) -> None:
        """Mark this password as compromised."""
        self.is_compromised = True
        if source:
            self.compromise_source = source
        self.policy_compliant = False
    
    def mark_replaced(self) -> None:
        """Mark this password as replaced."""
        self.replaced_at = datetime.utcnow()
    
    def increment_usage(self) -> None:
        """Increment usage count and update last used."""
        self.usage_count += 1
        self.last_used = datetime.utcnow()
    
    @classmethod
    def create_for_user(
        cls,
        user_id: uuid.UUID,
        password_hash: str,
        password_plain: str | None = None,
        change_reason: str | None = None,
        ip_address: str | None = None
    ) -> 'PasswordHistory':
        """
        Create a new password history entry.
        
        Args:
            user_id (uuid.UUID): The user ID
            password_hash (str): The hashed password
            password_plain (str, optional): Plain password for analysis
            change_reason (str, optional): Reason for change
            ip_address (str, optional): IP where change occurred
            
        Returns:
            PasswordHistory: New password history entry
        """
        entry = cls(
            user_id=user_id,
            password_hash=password_hash,
            set_at=datetime.utcnow(),
            change_reason=change_reason,
            ip_address=ip_address
        )
        
        # Analyze password if provided
        if password_plain:
            entry.analyze_password(password_plain)
        
        return entry
    
    def __repr__(self) -> str:
        """String representation of PasswordHistory."""
        return f"<PasswordHistory(id={self.id}, user_id={self.user_id}, strength={self.strength_level}, current={self.is_current})>"
