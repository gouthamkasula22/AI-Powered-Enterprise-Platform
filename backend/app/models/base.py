"""
Base Model Classes and Mixins

This module provides the foundational classes and mixins for all database models
in the User Authentication System. It includes common functionality like
timestamps, UUIDs, and soft deletion.

Author: User Authentication System
Version: 1.0.0
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class UUIDPrimaryKeyMixin:
    """Mixin that provides a UUID primary key."""
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
        doc="Unique identifier for the record"
    )


class TimestampMixin:
    """Mixin that provides created_at and updated_at timestamp fields."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Timestamp when the record was created"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when the record was last updated"
    )


class SoftDeleteMixin:
    """Mixin that provides soft deletion functionality."""
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when the record was soft-deleted"
    )
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="Flag indicating if the record is soft-deleted"
    )
    
    def soft_delete(self) -> None:
        """Mark the record as soft-deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None


class BaseModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Base model class that includes UUID primary key and timestamps.
    
    This is the standard base class for most models in the system.
    """
    __abstract__ = True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                # Convert datetime to ISO format for JSON serialization
                result[column.name] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                # Convert UUID to string for JSON serialization
                result[column.name] = str(value)
            else:
                result[column.name] = value
        return result
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """
        Update model instance from dictionary.
        
        Args:
            data (Dict[str, Any]): Dictionary with field names and values
        """
        for key, value in data.items():
            if hasattr(self, key) and key not in ('id', 'created_at'):
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


class SoftDeleteBaseModel(BaseModel, SoftDeleteMixin):
    """
    Base model class with soft deletion support.
    
    Use this for models that should support soft deletion.
    """
    __abstract__ = True


def generate_uuid() -> uuid.UUID:
    """
    Generate a new UUID4.
    
    Returns:
        uuid.UUID: A new UUID4 instance
    """
    return uuid.uuid4()


def utc_now() -> datetime:
    """
    Get current UTC timestamp.
    
    Returns:
        datetime: Current UTC datetime
    """
    return datetime.utcnow()


# Export commonly used classes and functions
__all__ = [
    'Base',
    'BaseModel',
    'SoftDeleteBaseModel',
    'UUIDPrimaryKeyMixin',
    'TimestampMixin',
    'SoftDeleteMixin',
    'generate_uuid',
    'utc_now'
]
