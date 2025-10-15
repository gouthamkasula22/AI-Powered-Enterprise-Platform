"""
Pytest Configuration for Integration Tests

Provides fixtures for testing FastAPI application endpoints.
"""

import pytest
import asyncio
import sys
import os
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

# Import the FastAPI app
try:
    from backend.src.presentation.main import app
    APP_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not import FastAPI app: {e}")
    APP_AVAILABLE = False
    app = None


# Configure asyncio event loop for tests
@pytest.fixture(scope="function")
def event_loop():
    """Create an event loop for each test function."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def client(event_loop) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing.
    
    If the FastAPI app is available, tests it directly using ASGI transport (high coverage).
    Otherwise, falls back to HTTP requests to localhost:8000 (tests endpoints only).
    """
    if APP_AVAILABLE and app is not None:
        # Use ASGI transport to test the app directly (better coverage)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac
    else:
        # Fall back to HTTP client (requires running server)
        async with AsyncClient(base_url="http://localhost:8000", timeout=5.0) as ac:
            yield ac


@pytest.fixture
def auth_headers():
    """Mock authentication headers for testing protected endpoints."""
    return {
        "Authorization": "Bearer mock_test_token"
    }
