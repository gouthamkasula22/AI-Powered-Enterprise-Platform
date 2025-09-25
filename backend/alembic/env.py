"""
Alembic Environment Configuration

This module provides the configuration for Alembic migrations in the
User Authentication System. It sets up async database connections and
ensures proper integration with SQLAlchemy models.

Author: User Authentication System
Version: 1.0.0
"""

from logging.config import fileConfig
from typing import Optional, Any, Dict
import asyncio
import logging
import os
import sys

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config, AsyncEngine
from alembic import context

# Add the parent directory to the Python path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import application components
try:
    from src.shared.config import get_settings
    from src.infrastructure.database.config import Base
    # Import all models to ensure they're in metadata
    from src.infrastructure.database.models import *
    settings = get_settings()
except ImportError as import_error:
    # Handle import errors gracefully during initial setup
    print(f"Warning: Could not import app modules: {import_error}")
    settings = None
    Base = None

# Configure logger
logger = logging.getLogger('alembic.env')

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the database URL from our settings if available
if settings:
    config.set_main_option("sqlalchemy.url", settings.database_url)
    logger.info(f"Using database URL from settings: {settings.database_url}")
else:
    logger.warning("Settings not available, using default database URL from alembic.ini")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata if Base else None

# Other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url() -> str:
    """
    Get the database URL for migrations.
    
    Returns:
        str: The database URL to use for migrations.
        
    Raises:
        ValueError: If no valid database URL is found.
    """
    # Try to get URL from settings first
    if settings and hasattr(settings, 'database_url'):
        return settings.database_url
    
    # Fallback to alembic.ini configuration
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return url
    
    raise ValueError("No database URL found in settings or alembic.ini")


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    try:
        url = get_database_url()
        logger.info(f"Running offline migrations with URL: {url}")
        
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,  # Support for SQLite if needed
        )

        with context.begin_transaction():
            context.run_migrations()
            
        logger.info("Offline migrations completed successfully")
        
    except Exception as error:
        logger.error(f"Error during offline migrations: {error}")
        raise


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations with the given connection.
    
    Args:
        connection: The database connection to use for migrations.
    """
    try:
        logger.info("Configuring migration context")
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,  # Support for SQLite if needed
        )

        with context.begin_transaction():
            logger.info("Running migrations")
            context.run_migrations()
            logger.info("Migrations completed successfully")
            
    except Exception as error:
        logger.error(f"Error during migration execution: {error}")
        raise


async def run_async_migrations() -> None:
    """
    Run migrations in async mode.
    
    This function creates an async engine and runs the migrations
    in a synchronous context.
    
    Raises:
        Exception: If migration fails for any reason.
    """
    try:
        logger.info("Starting async migrations")
        
        # Get configuration
        configuration = config.get_section(config.config_ini_section, {})
        configuration["sqlalchemy.url"] = get_database_url()
        
        # Create async engine
        connectable: AsyncEngine = async_engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        logger.info("Created async engine, establishing connection")
        
        async with connectable.connect() as connection:
            logger.info("Connected to database, running migrations")
            await connection.run_sync(do_run_migrations)

        logger.info("Disposing engine")
        await connectable.dispose()
        logger.info("Async migrations completed successfully")
        
    except Exception as error:
        logger.error(f"Error during async migrations: {error}")
        raise


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection
    with the context. This is the standard way to run migrations.
    """
    try:
        logger.info("Starting online migrations")
        asyncio.run(run_async_migrations())
    except Exception as error:
        logger.error(f"Error during online migrations: {error}")
        raise


# Determine migration mode and execute
if context.is_offline_mode():
    logger.info("Running in offline mode")
    run_migrations_offline()
else:
    logger.info("Running in online mode")
    run_migrations_online()
