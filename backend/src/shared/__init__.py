"""
Shared Components - Cross-cutting concerns
"""

# Import directly from config module to avoid circular imports
from .config import get_settings

__all__ = ["get_settings"]