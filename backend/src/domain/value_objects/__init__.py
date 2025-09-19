"""
Value Objects - Immutable objects with business validation
"""

from .email import Email
from .password import Password

__all__ = [
    "Email",
    "Password", 
]