"""
Base Repository pattern implementation for database operations
"""

from typing import Optional, Type, TypeVar, Generic, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine, async_sessionmaker
from contextlib import asynccontextmanager

from ..models import Base
from ....shared.config.settings import get_database_url

T = TypeVar('T', bound=Base)

class BaseRepository:
    """Base repository with common database operations"""
    
    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[async_sessionmaker] = None
    
    @classmethod
    def initialize(cls, database_url: Optional[str] = None):
        """Initialize the database connection"""
        if database_url is None:
            database_url = get_database_url()
        
        if database_url is not None:
            cls._engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)
        cls._session_factory = async_sessionmaker(
            bind=cls._engine, class_=AsyncSession, expire_on_commit=False
        )
    
    @classmethod
    @asynccontextmanager
    async def get_session(cls):
        """Get a database session as an async context manager"""
        if cls._session_factory is None:
            cls.initialize()
            
        if cls._session_factory is None:
            raise RuntimeError("Failed to initialize database session factory")
            
        async with cls._session_factory() as session:
            try:
                yield session
            finally:
                await session.close()