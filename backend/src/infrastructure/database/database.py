"""
Database Configuration and Connection Management

Handles SQLAlchemy engine, session creation, and database initialization.
"""

import logging
from typing import AsyncGenerator, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
import asyncio

from .models import Base
from ...shared.config import get_settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database connection and session management
    
    Handles database engine creation, session management, and connection lifecycle.
    """
    
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database connection and create tables"""
        if self._initialized:
            return
        
        try:
            settings = get_settings()
            
            # Create async engine
            if settings.debug:
                # For development, use NullPool to avoid connection issues
                self._engine = create_async_engine(
                    settings.database_url,
                    echo=settings.database_echo,
                    poolclass=NullPool,
                )
            else:
                # For production, use connection pooling
                self._engine = create_async_engine(
                    settings.database_url,
                    echo=settings.database_echo,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                )
            
            # Create async session factory
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create all tables
            await self.create_tables()
            
            self._initialized = True
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def create_tables(self) -> None:
        """Create all database tables"""
        if not self._engine:
            raise RuntimeError("Database engine not initialized")
        
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    async def drop_tables(self) -> None:
        """Drop all database tables (use with caution!)"""
        if not self._engine:
            raise RuntimeError("Database engine not initialized")
        
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session with proper cleanup
        
        Use this method to get a database session for operations.
        The session will be automatically closed when done.
        """
        if not self._session_factory:
            raise RuntimeError("Database not initialized")
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Close database connections"""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connections closed")
    
    @property
    def engine(self) -> Optional[AsyncEngine]:
        """Get the database engine"""
        return self._engine
    
    @property
    def is_initialized(self) -> bool:
        """Check if database is initialized"""
        return self._initialized


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function for FastAPI to get database session
    
    Usage in FastAPI endpoints:
    ```python
    async def my_endpoint(db: AsyncSession = Depends(get_db_session)):
        # Use db session here
    ```
    """
    db_manager = get_database_manager()
    if not db_manager.is_initialized:
        await db_manager.initialize()
    
    async for session in db_manager.get_session():
        yield session


async def initialize_database() -> None:
    """Initialize the database (call during app startup)"""
    db_manager = get_database_manager()
    await db_manager.initialize()


async def close_database() -> None:
    """Close database connections (call during app shutdown)"""
    db_manager = get_database_manager()
    await db_manager.close()


# Database health check
async def check_database_health() -> Dict[str, Any]:
    """
    Check database connectivity and return health status
    
    Returns:
        Dict with health information
    """
    try:
        db_manager = get_database_manager()
        
        if not db_manager.is_initialized:
            await db_manager.initialize()
        
        # Test database connection with a simple query
        async for session in db_manager.get_session():
            result = await session.execute(text("SELECT 1"))
            result.fetchone()
            
            return {
                "status": "healthy",
                "database": "connected",
                "tables_exist": True,
                "message": "Database is accessible"
            }
        
        # If we get here without returning, something went wrong
        return {
            "status": "unhealthy",
            "database": "unknown",
            "tables_exist": False,
            "message": "Could not establish database session"
        }
    
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "tables_exist": False,
            "message": f"Database error: {str(e)}"
        }


# Utility functions for testing
async def reset_database() -> None:
    """Reset database by dropping and recreating all tables"""
    db_manager = get_database_manager()
    await db_manager.drop_tables()
    await db_manager.create_tables()
    logger.info("Database reset completed")


async def seed_test_data() -> None:
    """Seed database with test data for development"""
    from .models import UserModel
    from ...domain.value_objects.password import Password
    from sqlalchemy import select
    
    try:
        async for session in get_db_session():
            # Check if test user already exists
            result = await session.execute(
                select(UserModel).where(UserModel.email == "test@example.com")
            )
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                # Create test password
                test_password = Password("TestPassword123!")
                
                # Create test user
                test_user = UserModel(
                    email="test@example.com",
                    password_hash=test_password.hash,
                    first_name="Test",
                    last_name="User",
                    username="testuser",
                    is_verified=True,
                    is_active=True
                )
                
                session.add(test_user)
                await session.commit()
                logger.info("Test user created: test@example.com / TestPassword123!")
            else:
                logger.info("Test user already exists")
                
    except Exception as e:
        logger.error(f"Failed to seed test data: {e}")
        raise