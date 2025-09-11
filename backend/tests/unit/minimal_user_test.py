"""
Minimal User Model for Testing
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel

class MinimalUser(BaseModel):
    """Minimal User model for testing."""
    __tablename__ = 'users_minimal'
    
    # Basic fields
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False
    )
    
    is_verified: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )
