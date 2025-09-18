"""
Test Configuration for Clean Architecture Backend

This module provides pytest configuration and shared fixtures for the
User Authentication System test suite using Clean Architecture.
"""

import asyncio
import os
import sys
import pytest

# Add the backend directory to Python path for clean architecture imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, 'backend')

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Verify the path exists
if not os.path.exists(backend_path):
    raise ImportError(f"Backend directory not found at: {backend_path}")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Create test-specific settings for clean architecture."""
    from src.shared.config import get_settings
    
    # Override settings for testing
    settings = get_settings()
    settings.ENVIRONMENT = "test"
    settings.DATABASE_URL = "postgresql+asyncpg://test_user:test_password@localhost:5432/test_auth_db"
    settings.DEBUG = True
    
    return settings


# TODO: Add more fixtures for clean architecture testing
# - Database session fixtures
# - Repository mock fixtures  
# - Use case test fixtures
# - Domain entity fixtures