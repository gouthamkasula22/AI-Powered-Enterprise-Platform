"""
Infrastructure Layer

This layer contains implementations of interfaces defined in the domain layer
and handles external concerns like databases, caching, email services, etc.

Components:
- database: PostgreSQL with SQLAlchemy async
- cache: Redis for caching and session management  
- email: SMTP and SendGrid email services
- security: JWT tokens and blacklisting
- external: Third-party service integrations
"""

from . import database, cache, email, security

__all__ = ["database", "cache", "email", "security"]