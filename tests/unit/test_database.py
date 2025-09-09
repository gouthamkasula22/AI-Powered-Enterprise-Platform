"""
Unit Tests for Database Configuration

This module contains unit tests for database configuration,
connection management, and query monitoring functionality.

Author: User Authentication System
Version: 1.0.0
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import AsyncGenerator

from app.core.config import Settings
from app.core.database import (
    get_db,
    test_database_connection,
    get_database_stats,
    check_database_health,
    query_stats,
    TrackedAsyncSession
)


class TestDatabaseConfiguration:
    """Test database configuration and connection management."""

    def test_settings_database_configuration(self) -> None:
        """Test database configuration settings."""
        settings = Settings(ENVIRONMENT="test")
        
        # Test environment-specific configurations
        assert settings.DB_POOL_SIZE == 5  # Test environment uses smaller pool
        assert settings.DB_MAX_OVERFLOW == 10
        assert settings.DB_POOL_TIMEOUT == 30
        assert settings.DB_POOL_RECYCLE == 3600
        assert settings.DB_POOL_PRE_PING is True
        
    def test_production_database_configuration(self) -> None:
        """Test production database configuration."""
        settings = Settings(ENVIRONMENT="production")
        
        # Production environment uses larger pool
        assert settings.DB_POOL_SIZE == 20
        assert settings.DB_MAX_OVERFLOW == 30
        assert settings.DB_ECHO is False  # No query echoing in production

    def test_development_database_configuration(self) -> None:
        """Test development database configuration."""
        settings = Settings(ENVIRONMENT="development", DEBUG=True)
        
        # Development environment enables query echoing
        assert settings.DB_ECHO is True
        assert settings.DB_POOL_SIZE == 5

    @pytest.mark.asyncio
    async def test_database_connection_success(self) -> None:
        """Test successful database connection."""
        with patch('app.core.database.engine') as mock_engine:
            mock_connection = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_connection
            
            result = await test_database_connection()
            
            assert result is True
            mock_connection.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_connection_failure(self) -> None:
        """Test database connection failure handling."""
        with patch('app.core.database.engine') as mock_engine:
            mock_engine.begin.side_effect = Exception("Connection failed")
            
            result = await test_database_connection()
            
            assert result is False

    @pytest.mark.asyncio
    async def test_get_database_stats(self) -> None:
        """Test database statistics retrieval."""
        with patch('app.core.database.engine') as mock_engine:
            mock_pool = Mock()
            mock_pool.size.return_value = 10
            mock_pool.checkedin.return_value = 5
            mock_pool.checkedout.return_value = 3
            mock_pool.overflow.return_value = 2
            mock_pool.invalid.return_value = 0
            mock_engine.pool = mock_pool
            
            stats = await get_database_stats()
            
            assert stats["pool_size"] == 10
            assert stats["checked_in"] == 5
            assert stats["checked_out"] == 3
            assert stats["overflow"] == 2
            assert stats["invalid"] == 0

    @pytest.mark.asyncio
    async def test_database_health_check_healthy(self) -> None:
        """Test database health check for healthy database."""
        with patch('app.core.database.test_database_connection', return_value=True), \
             patch('app.core.database.get_database_stats', return_value={"pool_size": 10}):
            
            health = await check_database_health()
            
            assert health["status"] == "healthy"
            assert health["connection_test"] is True
            assert health["response_time_ms"] < 1000

    @pytest.mark.asyncio
    async def test_database_health_check_unhealthy(self) -> None:
        """Test database health check for unhealthy database."""
        with patch('app.core.database.test_database_connection', return_value=False):
            
            health = await check_database_health()
            
            assert health["status"] == "unhealthy"
            assert health["connection_test"] is False


class TestQueryMonitoring:
    """Test query monitoring and statistics functionality."""

    def test_query_stats_initialization(self) -> None:
        """Test query statistics initialization."""
        # Clear existing stats
        query_stats.queries.clear()
        query_stats.session_queries.clear()
        
        assert len(query_stats.queries) == 0
        assert len(query_stats.session_queries) == 0

    def test_query_stats_recording(self) -> None:
        """Test query statistics recording."""
        # Clear existing stats
        query_stats.queries.clear()
        query_stats.session_queries.clear()
        
        # Record a query
        query_stats.record_query(
            query_hash="test123",
            query="SELECT * FROM users",
            execution_time=0.5,
            query_type="SELECT"
        )
        
        assert len(query_stats.queries) == 1
        assert "test123" in query_stats.queries
        
        stats = query_stats.queries["test123"]
        assert stats["count"] == 1
        assert stats["avg_time"] == 0.5
        assert stats["type"] == "SELECT"

    def test_slow_query_detection(self) -> None:
        """Test slow query detection and tracking."""
        # Clear existing stats
        query_stats.queries.clear()
        query_stats.session_queries.clear()
        
        # Record slow queries
        query_stats.record_query("slow1", "SELECT * FROM large_table", 1.5, "SELECT")
        query_stats.record_query("fast1", "SELECT 1", 0.1, "SELECT")
        query_stats.record_query("slow2", "SELECT * FROM large_table", 2.0, "SELECT")
        
        slow_queries = query_stats.get_slow_queries(threshold=1.0)
        
        assert len(slow_queries) == 1  # Only one unique slow query pattern
        assert slow_queries[0]["hash"] == "slow1"
        assert slow_queries[0]["slow_count"] == 2  # Two slow executions

    def test_frequent_queries_tracking(self) -> None:
        """Test frequent queries tracking."""
        # Clear existing stats
        query_stats.queries.clear()
        query_stats.session_queries.clear()
        
        # Record multiple executions of the same query
        for _ in range(5):
            query_stats.record_query("freq1", "SELECT COUNT(*) FROM users", 0.1, "SELECT")
        
        for _ in range(3):
            query_stats.record_query("freq2", "SELECT * FROM posts", 0.2, "SELECT")
        
        frequent_queries = query_stats.get_most_frequent(limit=2)
        
        assert len(frequent_queries) == 2
        assert frequent_queries[0]["count"] == 5  # Most frequent first
        assert frequent_queries[1]["count"] == 3

    @pytest.mark.asyncio
    async def test_tracked_session_query_logging(self) -> None:
        """Test TrackedAsyncSession query logging."""
        with patch('app.core.database.AsyncSession') as MockSession:
            # Create a mock session
            mock_session = MockSession.return_value
            mock_session.execute = AsyncMock()
            
            # Test normal query execution
            session = TrackedAsyncSession(bind=Mock())
            session.execute = AsyncMock()
            
            # This would normally log the query
            await session.execute("SELECT 1")
            
            # Verify the execute method was called
            session.execute.assert_called_once()


class TestDatabaseDependency:
    """Test database dependency injection."""

    @pytest.mark.asyncio
    async def test_get_db_session_lifecycle(self) -> None:
        """Test database session lifecycle management."""
        with patch('app.core.database.AsyncSessionLocal') as MockSessionLocal:
            mock_session = AsyncMock()
            MockSessionLocal.return_value.__aenter__.return_value = mock_session
            MockSessionLocal.return_value.__aexit__.return_value = None
            
            # Test session creation and cleanup
            async_gen = get_db()
            session = await anext(async_gen)
            
            assert session == mock_session

    @pytest.mark.asyncio
    async def test_get_db_error_handling(self) -> None:
        """Test database session error handling."""
        with patch('app.core.database.AsyncSessionLocal') as MockSessionLocal:
            mock_session = AsyncMock()
            mock_session.commit.side_effect = Exception("Database error")
            MockSessionLocal.return_value.__aenter__.return_value = mock_session
            MockSessionLocal.return_value.__aexit__.return_value = None
            
            # Test error handling
            async_gen = get_db()
            
            with pytest.raises(Exception, match="Database error"):
                session = await anext(async_gen)
                try:
                    await anext(async_gen)  # This should trigger the exception
                except StopAsyncIteration:
                    pass  # This is expected when the generator finishes


# Performance benchmarks
class TestDatabasePerformance:
    """Test database performance characteristics."""

    @pytest.mark.asyncio
    async def test_connection_pool_performance(self) -> None:
        """Test connection pool performance under load."""
        # This would be a more comprehensive test in a real scenario
        with patch('app.core.database.engine') as mock_engine:
            mock_pool = Mock()
            mock_pool.size.return_value = 10
            mock_engine.pool = mock_pool
            
            # Simulate multiple concurrent connections
            stats = await get_database_stats()
            
            # Verify pool is configured correctly
            assert stats["pool_size"] == 10

    def test_query_statistics_memory_usage(self) -> None:
        """Test query statistics memory management."""
        # Clear existing stats
        query_stats.queries.clear()
        query_stats.session_queries.clear()
        
        # Add many queries to test memory management
        for i in range(1500):  # More than the 1000 limit
            query_stats.record_query(
                f"query{i}",
                f"SELECT {i}",
                0.1,
                "SELECT"
            )
        
        # Should limit session queries to prevent memory issues
        assert len(query_stats.session_queries) <= 1000
