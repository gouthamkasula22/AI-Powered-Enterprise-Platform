"""
Migration Utilities

This module provides utilities for database migrations, including
backup functionality, migration validation, and rollback utilities
for the User Authentication System.

Author: User Authentication System
Version: 1.0.0
"""

import asyncio
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json
import os

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy import text
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from app.core.config import settings
from app.core.database import engine

# Configure logger
logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Custom exception for migration-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize migration error.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.details = details or {}


class MigrationManager:
    """
    Professional migration management utilities.
    
    Provides comprehensive migration operations including backup,
    validation, and rollback functionality.
    """
    
    def __init__(self, alembic_cfg_path: str = "alembic.ini") -> None:
        """
        Initialize migration manager.
        
        Args:
            alembic_cfg_path: Path to alembic configuration file
        """
        self.alembic_cfg_path = alembic_cfg_path
        self.alembic_cfg = Config(alembic_cfg_path)
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
    async def get_current_revision(self) -> Optional[str]:
        """
        Get current database revision.
        
        Returns:
            Current revision ID or None if no migrations applied
            
        Raises:
            MigrationError: If unable to determine current revision
        """
        try:
            async with engine.connect() as connection:
                # Run sync operation to get migration context
                def get_revision(conn):
                    context = MigrationContext.configure(conn)
                    return context.get_current_revision()
                
                revision = await connection.run_sync(get_revision)
                logger.info(f"Current database revision: {revision}")
                return revision
                
        except Exception as error:
            logger.error(f"Failed to get current revision: {error}")
            raise MigrationError(
                "Could not determine current database revision",
                {"error": str(error)}
            ) from error
    
    async def get_pending_migrations(self) -> List[str]:
        """
        Get list of pending migrations.
        
        Returns:
            List of pending migration revision IDs
            
        Raises:
            MigrationError: If unable to determine pending migrations
        """
        try:
            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            current_rev = await self.get_current_revision()
            
            # Get all revisions from current to head
            revisions = []
            for revision in script_dir.walk_revisions(current_rev, "heads"):
                if revision.revision != current_rev:
                    revisions.append(revision.revision)
            
            logger.info(f"Found {len(revisions)} pending migrations")
            return revisions
            
        except Exception as error:
            logger.error(f"Failed to get pending migrations: {error}")
            raise MigrationError(
                "Could not determine pending migrations",
                {"error": str(error)}
            ) from error
    
    def create_database_backup(self, backup_name: Optional[str] = None) -> str:
        """
        Create database backup before migration.
        
        Args:
            backup_name: Optional custom backup name
            
        Returns:
            Path to the created backup file
            
        Raises:
            MigrationError: If backup creation fails
        """
        try:
            if backup_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}.sql"
            
            backup_path = self.backup_dir / backup_name
            
            # Extract database connection details
            db_url = settings.DATABASE_URL
            if not db_url.startswith("postgresql"):
                logger.warning("Backup only supported for PostgreSQL databases")
                return str(backup_path)
            
            # Parse connection details (simplified for PostgreSQL)
            # In production, use proper URL parsing
            cmd = [
                "pg_dump",
                "--no-password",
                "--verbose",
                "--file", str(backup_path),
                db_url.replace("postgresql+asyncpg://", "postgresql://")
            ]
            
            logger.info(f"Creating database backup: {backup_path}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.returncode == 0:
                logger.info(f"Database backup created successfully: {backup_path}")
                return str(backup_path)
            else:
                raise MigrationError(
                    "Database backup failed",
                    {"stderr": result.stderr, "stdout": result.stdout}
                )
                
        except subprocess.CalledProcessError as error:
            logger.error(f"Backup process failed: {error}")
            raise MigrationError(
                "Database backup process failed",
                {"error": str(error), "stderr": error.stderr}
            ) from error
        except Exception as error:
            logger.error(f"Unexpected error during backup: {error}")
            raise MigrationError(
                "Unexpected error during database backup",
                {"error": str(error)}
            ) from error
    
    async def validate_migration(self, target_revision: str) -> bool:
        """
        Validate migration before applying.
        
        Args:
            target_revision: Target revision to validate
            
        Returns:
            True if migration is valid
            
        Raises:
            MigrationError: If validation fails
        """
        try:
            logger.info(f"Validating migration to revision: {target_revision}")
            
            # Check if target revision exists
            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            try:
                script_dir.get_revision(target_revision)
            except Exception as error:
                raise MigrationError(
                    f"Target revision {target_revision} not found",
                    {"error": str(error)}
                ) from error
            
            # Validate database connection
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            
            logger.info("Migration validation passed")
            return True
            
        except Exception as error:
            logger.error(f"Migration validation failed: {error}")
            raise MigrationError(
                f"Migration validation failed for revision {target_revision}",
                {"error": str(error)}
            ) from error
    
    def apply_migration(self, target_revision: str = "head") -> bool:
        """
        Apply migration to target revision.
        
        Args:
            target_revision: Target revision (default: "head")
            
        Returns:
            True if migration successful
            
        Raises:
            MigrationError: If migration fails
        """
        try:
            logger.info(f"Applying migration to: {target_revision}")
            
            # Apply migration using Alembic command
            command.upgrade(self.alembic_cfg, target_revision)
            
            logger.info(f"Migration to {target_revision} completed successfully")
            return True
            
        except Exception as error:
            logger.error(f"Migration failed: {error}")
            raise MigrationError(
                f"Failed to apply migration to {target_revision}",
                {"error": str(error)}
            ) from error
    
    def rollback_migration(self, target_revision: str) -> bool:
        """
        Rollback migration to target revision.
        
        Args:
            target_revision: Target revision to rollback to
            
        Returns:
            True if rollback successful
            
        Raises:
            MigrationError: If rollback fails
        """
        try:
            logger.info(f"Rolling back migration to: {target_revision}")
            
            # Rollback using Alembic downgrade command
            command.downgrade(self.alembic_cfg, target_revision)
            
            logger.info(f"Rollback to {target_revision} completed successfully")
            return True
            
        except Exception as error:
            logger.error(f"Rollback failed: {error}")
            raise MigrationError(
                f"Failed to rollback to {target_revision}",
                {"error": str(error)}
            ) from error
    
    def generate_migration(self, message: str, autogenerate: bool = True) -> str:
        """
        Generate new migration.
        
        Args:
            message: Migration message
            autogenerate: Whether to auto-generate migration content
            
        Returns:
            Generated migration revision ID
            
        Raises:
            MigrationError: If migration generation fails
        """
        try:
            logger.info(f"Generating migration: {message}")
            
            # Generate migration using Alembic revision command
            if autogenerate:
                revision = command.revision(
                    self.alembic_cfg,
                    message=message,
                    autogenerate=True
                )
            else:
                revision = command.revision(
                    self.alembic_cfg,
                    message=message
                )
            
            # Extract revision ID from the returned object
            revision_id = revision.revision if hasattr(revision, 'revision') else str(revision)
            
            logger.info(f"Migration generated successfully: {revision_id}")
            return revision_id
            
        except Exception as error:
            logger.error(f"Migration generation failed: {error}")
            raise MigrationError(
                f"Failed to generate migration: {message}",
                {"error": str(error)}
            ) from error
    
    async def get_migration_history(self) -> List[Dict[str, Any]]:
        """
        Get migration history.
        
        Returns:
            List of migration history entries
            
        Raises:
            MigrationError: If unable to retrieve history
        """
        try:
            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            current_rev = await self.get_current_revision()
            
            history = []
            for revision in script_dir.walk_revisions():
                history.append({
                    "revision": revision.revision,
                    "down_revision": revision.down_revision,
                    "branch_labels": revision.branch_labels,
                    "depends_on": revision.depends_on,
                    "doc": revision.doc,
                    "is_current": revision.revision == current_rev
                })
            
            logger.info(f"Retrieved {len(history)} migration history entries")
            return history
            
        except Exception as error:
            logger.error(f"Failed to get migration history: {error}")
            raise MigrationError(
                "Could not retrieve migration history",
                {"error": str(error)}
            ) from error


# Global migration manager instance
migration_manager = MigrationManager()


async def safe_migrate_to_head() -> Tuple[bool, Optional[str]]:
    """
    Safely migrate database to head with backup.
    
    Returns:
        Tuple of (success, backup_path)
        
    Raises:
        MigrationError: If migration fails
    """
    backup_path = None
    
    try:
        logger.info("Starting safe migration to head")
        
        # Check for pending migrations
        pending = await migration_manager.get_pending_migrations()
        if not pending:
            logger.info("No pending migrations found")
            return True, None
        
        logger.info(f"Found {len(pending)} pending migrations")
        
        # Create backup
        backup_path = migration_manager.create_database_backup()
        
        # Validate migration
        await migration_manager.validate_migration("head")
        
        # Apply migration
        success = migration_manager.apply_migration("head")
        
        if success:
            logger.info("Safe migration to head completed successfully")
            return True, backup_path
        else:
            raise MigrationError("Migration to head failed")
            
    except Exception as error:
        logger.error(f"Safe migration failed: {error}")
        raise MigrationError(
            "Safe migration to head failed",
            {"error": str(error), "backup_path": backup_path}
        ) from error


async def get_migration_status() -> Dict[str, Any]:
    """
    Get comprehensive migration status.
    
    Returns:
        Dictionary containing migration status information
    """
    try:
        current_rev = await migration_manager.get_current_revision()
        pending_migrations = await migration_manager.get_pending_migrations()
        history = await migration_manager.get_migration_history()
        
        return {
            "current_revision": current_rev,
            "pending_migrations": pending_migrations,
            "total_migrations": len(history),
            "needs_migration": len(pending_migrations) > 0,
            "database_url": settings.DATABASE_URL,
            "alembic_config": migration_manager.alembic_cfg_path
        }
        
    except Exception as error:
        logger.error(f"Failed to get migration status: {error}")
        return {
            "error": str(error),
            "current_revision": None,
            "pending_migrations": [],
            "total_migrations": 0,
            "needs_migration": False
        }
