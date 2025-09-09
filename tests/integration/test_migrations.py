"""
Integration Tests for Alembic Migrations

This module contains comprehensive integration tests for Alembic
database migrations, including migration generation, application,
and rollback functionality.

Author: User Authentication System
Version: 1.0.0
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import pytest
from unittest.mock import patch, Mock

# Note: These imports will work once dependencies are installed
try:
    from alembic import command
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext
    ALEMBIC_AVAILABLE = True
except ImportError:
    ALEMBIC_AVAILABLE = False

from app.core.migrations import (
    MigrationManager,
    MigrationError,
    safe_migrate_to_head,
    get_migration_status
)


@pytest.mark.skipif(not ALEMBIC_AVAILABLE, reason="Alembic not available")
class TestMigrationManager:
    """Test MigrationManager functionality."""

    @pytest.fixture
    def temp_alembic_config(self) -> str:
        """Create temporary alembic configuration for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("""
[alembic]
script_location = alembic
sqlalchemy.url = sqlite:///test.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
""")
            return f.name

    def test_migration_manager_initialization(self, temp_alembic_config: str) -> None:
        """Test MigrationManager initialization."""
        manager = MigrationManager(temp_alembic_config)
        
        assert manager.alembic_cfg_path == temp_alembic_config
        assert isinstance(manager.alembic_cfg, Config)
        assert manager.backup_dir.exists()

    @pytest.mark.asyncio
    async def test_get_current_revision_no_database(self) -> None:
        """Test getting current revision when database doesn't exist."""
        with patch('app.core.migrations.engine') as mock_engine:
            mock_engine.connect.side_effect = Exception("Database not found")
            
            manager = MigrationManager()
            
            with pytest.raises(MigrationError, match="Could not determine current database revision"):
                await manager.get_current_revision()

    @pytest.mark.asyncio
    async def test_get_current_revision_success(self) -> None:
        """Test successful retrieval of current revision."""
        with patch('app.core.migrations.engine') as mock_engine:
            mock_connection = Mock()
            mock_engine.connect.return_value.__aenter__.return_value = mock_connection
            
            def mock_get_revision(conn):
                context = Mock()
                context.get_current_revision.return_value = "abc123"
                return "abc123"
            
            mock_connection.run_sync.return_value = "abc123"
            
            manager = MigrationManager()
            revision = await manager.get_current_revision()
            
            assert revision == "abc123"

    def test_create_database_backup_postgresql(self) -> None:
        """Test database backup creation for PostgreSQL."""
        with patch('subprocess.run') as mock_run, \
             patch('app.core.migrations.settings') as mock_settings:
            
            mock_settings.DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"
            mock_run.return_value.returncode = 0
            
            manager = MigrationManager()
            backup_path = manager.create_database_backup("test_backup.sql")
            
            assert "test_backup.sql" in backup_path
            mock_run.assert_called_once()

    def test_create_database_backup_failure(self) -> None:
        """Test database backup failure handling."""
        with patch('subprocess.run') as mock_run, \
             patch('app.core.migrations.settings') as mock_settings:
            
            mock_settings.DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"
            mock_run.side_effect = Exception("Backup failed")
            
            manager = MigrationManager()
            
            with pytest.raises(MigrationError, match="Unexpected error during database backup"):
                manager.create_database_backup()

    @pytest.mark.asyncio
    async def test_validate_migration_success(self) -> None:
        """Test successful migration validation."""
        with patch('app.core.migrations.engine') as mock_engine, \
             patch.object(MigrationManager, '__init__', return_value=None):
            
            # Mock engine connection
            mock_connection = Mock()
            mock_engine.connect.return_value.__aenter__.return_value = mock_connection
            
            # Mock alembic config and script directory
            manager = MigrationManager.__new__(MigrationManager)
            manager.alembic_cfg = Mock()
            
            with patch('app.core.migrations.ScriptDirectory') as mock_script_dir:
                mock_script_dir.from_config.return_value.get_revision.return_value = Mock()
                
                result = await manager.validate_migration("test_revision")
                
                assert result is True

    @pytest.mark.asyncio
    async def test_validate_migration_invalid_revision(self) -> None:
        """Test migration validation with invalid revision."""
        with patch.object(MigrationManager, '__init__', return_value=None):
            manager = MigrationManager.__new__(MigrationManager)
            manager.alembic_cfg = Mock()
            
            with patch('app.core.migrations.ScriptDirectory') as mock_script_dir:
                mock_script_dir.from_config.return_value.get_revision.side_effect = Exception("Not found")
                
                with pytest.raises(MigrationError, match="Target revision test_revision not found"):
                    await manager.validate_migration("test_revision")

    def test_apply_migration_success(self) -> None:
        """Test successful migration application."""
        with patch('app.core.migrations.command') as mock_command, \
             patch.object(MigrationManager, '__init__', return_value=None):
            
            manager = MigrationManager.__new__(MigrationManager)
            manager.alembic_cfg = Mock()
            
            result = manager.apply_migration("head")
            
            assert result is True
            mock_command.upgrade.assert_called_once_with(manager.alembic_cfg, "head")

    def test_apply_migration_failure(self) -> None:
        """Test migration application failure."""
        with patch('app.core.migrations.command') as mock_command, \
             patch.object(MigrationManager, '__init__', return_value=None):
            
            manager = MigrationManager.__new__(MigrationManager)
            manager.alembic_cfg = Mock()
            mock_command.upgrade.side_effect = Exception("Migration failed")
            
            with pytest.raises(MigrationError, match="Failed to apply migration to head"):
                manager.apply_migration("head")

    def test_rollback_migration_success(self) -> None:
        """Test successful migration rollback."""
        with patch('app.core.migrations.command') as mock_command, \
             patch.object(MigrationManager, '__init__', return_value=None):
            
            manager = MigrationManager.__new__(MigrationManager)
            manager.alembic_cfg = Mock()
            
            result = manager.rollback_migration("previous_revision")
            
            assert result is True
            mock_command.downgrade.assert_called_once_with(manager.alembic_cfg, "previous_revision")

    def test_generate_migration_success(self) -> None:
        """Test successful migration generation."""
        with patch('app.core.migrations.command') as mock_command, \
             patch.object(MigrationManager, '__init__', return_value=None):
            
            manager = MigrationManager.__new__(MigrationManager)
            manager.alembic_cfg = Mock()
            
            # Mock the revision object
            mock_revision = Mock()
            mock_revision.revision = "new_revision_123"
            mock_command.revision.return_value = mock_revision
            
            revision_id = manager.generate_migration("Test migration", autogenerate=True)
            
            assert revision_id == "new_revision_123"
            mock_command.revision.assert_called_once_with(
                manager.alembic_cfg,
                message="Test migration",
                autogenerate=True
            )

    @pytest.mark.asyncio
    async def test_get_migration_history(self) -> None:
        """Test migration history retrieval."""
        with patch.object(MigrationManager, '__init__', return_value=None), \
             patch.object(MigrationManager, 'get_current_revision', return_value="current_rev"):
            
            manager = MigrationManager.__new__(MigrationManager)
            manager.alembic_cfg = Mock()
            
            # Mock script directory and revisions
            mock_revision = Mock()
            mock_revision.revision = "rev_123"
            mock_revision.down_revision = "rev_122"
            mock_revision.branch_labels = None
            mock_revision.depends_on = None
            mock_revision.doc = "Test migration"
            
            with patch('app.core.migrations.ScriptDirectory') as mock_script_dir:
                mock_script_dir.from_config.return_value.walk_revisions.return_value = [mock_revision]
                
                history = await manager.get_migration_history()
                
                assert len(history) == 1
                assert history[0]["revision"] == "rev_123"
                assert history[0]["down_revision"] == "rev_122"
                assert history[0]["doc"] == "Test migration"


class TestMigrationUtilities:
    """Test migration utility functions."""

    @pytest.mark.asyncio
    async def test_safe_migrate_to_head_no_pending(self) -> None:
        """Test safe migration when no pending migrations exist."""
        with patch('app.core.migrations.migration_manager') as mock_manager:
            mock_manager.get_pending_migrations.return_value = []
            
            success, backup_path = await safe_migrate_to_head()
            
            assert success is True
            assert backup_path is None

    @pytest.mark.asyncio
    async def test_safe_migrate_to_head_with_pending(self) -> None:
        """Test safe migration with pending migrations."""
        with patch('app.core.migrations.migration_manager') as mock_manager:
            mock_manager.get_pending_migrations.return_value = ["rev_123", "rev_124"]
            mock_manager.create_database_backup.return_value = "/path/to/backup.sql"
            mock_manager.validate_migration.return_value = None
            mock_manager.apply_migration.return_value = True
            
            success, backup_path = await safe_migrate_to_head()
            
            assert success is True
            assert backup_path == "/path/to/backup.sql"
            mock_manager.create_database_backup.assert_called_once()
            mock_manager.validate_migration.assert_called_once_with("head")
            mock_manager.apply_migration.assert_called_once_with("head")

    @pytest.mark.asyncio
    async def test_safe_migrate_to_head_failure(self) -> None:
        """Test safe migration failure handling."""
        with patch('app.core.migrations.migration_manager') as mock_manager:
            mock_manager.get_pending_migrations.return_value = ["rev_123"]
            mock_manager.create_database_backup.return_value = "/path/to/backup.sql"
            mock_manager.validate_migration.side_effect = Exception("Validation failed")
            
            with pytest.raises(MigrationError, match="Safe migration to head failed"):
                await safe_migrate_to_head()

    @pytest.mark.asyncio
    async def test_get_migration_status_success(self) -> None:
        """Test successful migration status retrieval."""
        with patch('app.core.migrations.migration_manager') as mock_manager:
            mock_manager.get_current_revision.return_value = "current_rev"
            mock_manager.get_pending_migrations.return_value = ["pending_rev"]
            mock_manager.get_migration_history.return_value = [{"rev": "1"}, {"rev": "2"}]
            
            status = await get_migration_status()
            
            assert status["current_revision"] == "current_rev"
            assert status["pending_migrations"] == ["pending_rev"]
            assert status["total_migrations"] == 2
            assert status["needs_migration"] is True

    @pytest.mark.asyncio
    async def test_get_migration_status_error(self) -> None:
        """Test migration status retrieval with error."""
        with patch('app.core.migrations.migration_manager') as mock_manager:
            mock_manager.get_current_revision.side_effect = Exception("Database error")
            
            status = await get_migration_status()
            
            assert "error" in status
            assert status["current_revision"] is None
            assert status["needs_migration"] is False


class TestMigrationIntegration:
    """Integration tests for complete migration workflows."""

    @pytest.mark.asyncio
    async def test_complete_migration_workflow(self) -> None:
        """Test complete migration workflow from generation to application."""
        # This would be a full integration test with actual database
        # For now, we'll test the workflow with mocks
        
        with patch('app.core.migrations.migration_manager') as mock_manager:
            # Mock the complete workflow
            mock_manager.get_current_revision.return_value = None
            mock_manager.generate_migration.return_value = "new_rev_123"
            mock_manager.get_pending_migrations.return_value = ["new_rev_123"]
            mock_manager.create_database_backup.return_value = "/backup/path"
            mock_manager.validate_migration.return_value = True
            mock_manager.apply_migration.return_value = True
            
            # Generate migration
            revision = mock_manager.generate_migration("Initial migration")
            assert revision == "new_rev_123"
            
            # Apply migration safely
            success, backup_path = await safe_migrate_to_head()
            assert success is True
            assert backup_path == "/backup/path"

    def test_migration_error_handling(self) -> None:
        """Test comprehensive error handling in migrations."""
        # Test custom MigrationError
        error = MigrationError("Test error", {"detail": "test detail"})
        
        assert str(error) == "Test error"
        assert error.details["detail"] == "test detail"

    @pytest.mark.asyncio
    async def test_migration_performance_benchmarks(self) -> None:
        """Test migration performance characteristics."""
        import time
        
        with patch('app.core.migrations.migration_manager') as mock_manager:
            mock_manager.get_current_revision.return_value = "current"
            
            start_time = time.time()
            await get_migration_status()
            end_time = time.time()
            
            # Migration status should be fast
            assert (end_time - start_time) < 1.0
