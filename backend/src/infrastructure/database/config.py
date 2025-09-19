"""
Database Configuration and Session Management

Provides database configuration, connection management, and session handling
for the infrastructure layer.
"""

from datetime import datetime
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


class BaseModel(Base):
    """
    Base model with common fields for all entities
    """
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class DatabaseConfig:
    """Database configuration and session management"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for SQL logging in development
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a new database session"""
        async with self.async_session_factory() as session:
            yield session
    
    async def close(self):
        """Close the database engine"""
        await self.engine.dispose()


# Global database instance (will be configured by dependency injection)
_db_config: DatabaseConfig | None = None


def configure_database(database_url: str) -> DatabaseConfig:
    """Configure the global database instance"""
    global _db_config
    _db_config = DatabaseConfig(database_url)
    return _db_config


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection function for database sessions"""
    if _db_config is None:
        raise RuntimeError("Database not configured. Call configure_database() first.")
    
    async for session in _db_config.get_session():
        yield session