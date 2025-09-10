"""
User Model - Clean Version for M1.2

Core User model with essential fields for authentication.
This is the working version that passes all M1.2 validation tests.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel


class User(BaseModel):
    """
    Core User model with essential fields for authentication
    """
    __tablename__ = "users"
    
    # Core authentication field
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        index=True, 
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
