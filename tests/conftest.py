"""
Test Configuration and Fixtures

This module provides pytest configuration and shared fixtures for the
User Authentication System test suite.
"""

import asyncio
import os
import pytest
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.core.database import Base, get_db
from app.main import create_app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Create test-specific settings."""
    return Settings(
        ENVIRONMENT="test",
        DEBUG=True,
        DATABASE_URL="postgresql+asyncpg://test_user:test_password@localhost:5432/test_auth_db",
        SECRET_KEY="test-secret-key-for-testing-only",
        LOG_LEVEL="DEBUG"
    )


@pytest.fixture(scope="session")
async def test_engine(test_settings: Settings):
    """Create test database engine."""
    engine = create_async_engine(
        test_settings.DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Don't pool connections in tests
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def test_app(test_settings: Settings):
    """Create test FastAPI application."""
    # Override settings for testing
    from app.core import config
    original_settings = config.settings
    config.settings = test_settings
    
    app = create_app()
    
    yield app
    
    # Restore original settings
    config.settings = original_settings


@pytest.fixture
async def test_client(test_app, test_session: AsyncSession):
    """Create test HTTP client with database session override."""
    from fastapi.testclient import TestClient
    
    # Override database dependency
    async def override_get_db():
        yield test_session
    
    test_app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(test_app) as client:
        yield client
    
    # Cleanup
    test_app.dependency_overrides.clear()
