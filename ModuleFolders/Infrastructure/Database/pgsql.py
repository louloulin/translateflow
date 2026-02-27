# ModuleFolders/Infrastructure/Database/pgsql.py
"""
PostgreSQL database configuration with connection pooling.

Environment variables:
    - DATABASE_URL: PostgreSQL connection URL (required for PostgreSQL)
    - DB_HOST: Database host (default: localhost)
    - DB_PORT: Database port (default: 5432)
    - DB_NAME: Database name (default: ainiee)
    - DB_USER: Database user (default: postgres)
    - DB_PASSWORD: Database password (required)
    - USE_SQLITE: Set to 'true' to use SQLite instead (fallback)
    - SQLITE_PATH: Path to SQLite file (default: ainiee.db)
"""

import os
from typing import Optional
from urllib.parse import urlparse

from peewee import PostgresqlDatabase, SqliteDatabase
from playhouse.pool import PooledPostgresqlDatabase


def get_database_url() -> Optional[str]:
    """Get DATABASE_URL from environment."""
    return os.getenv("DATABASE_URL")


def get_database_config() -> dict:
    """
    Get database configuration from environment variables.

    Returns:
        Dictionary with database connection parameters.
    """
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "database": os.getenv("DB_NAME", "ainiee"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
    }


def parse_database_url(url: str) -> dict:
    """
    Parse DATABASE_URL into connection parameters.

    Args:
        url: PostgreSQL connection URL (postgresql://user:pass@host:port/db)

    Returns:
        Dictionary with connection parameters.
    """
    parsed = urlparse(url)

    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/") if parsed.path else "ainiee",
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
    }


def should_use_sqlite() -> bool:
    """
    Check if SQLite should be used instead of PostgreSQL.

    Returns:
        True if USE_SQLITE is set to 'true' or '1'.
    """
    return os.getenv("USE_SQLITE", "").lower() in ("true", "1", "yes")


def get_sqlite_path() -> str:
    """Get SQLite database file path from environment."""
    return os.getenv("SQLITE_PATH", "ainiee.db")


def create_postgresql_database(config: dict) -> PooledPostgresqlDatabase:
    """
    Create PostgreSQL database with connection pooling.

    Args:
        config: Database configuration dictionary.

    Returns:
        PooledPostgresqlDatabase instance.
    """
    return PooledPostgresqlDatabase(
        config["database"],
        user=config["user"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
        max_connections=10,  # Maximum connection pool size
        stale_timeout=300,   # Close stale connections after 5 minutes
        timeout=10,          # Connection timeout in seconds
    )


def create_sqlite_database(path: str) -> SqliteDatabase:
    """
    Create SQLite database.

    Args:
        path: Path to SQLite database file.

    Returns:
        SqliteDatabase instance.
    """
    return SqliteDatabase(
        path,
        pragmas={
            "journal_mode": "WAL",  # Write-Ahead Logging for better concurrency
            "cache_size": -1024 * 64,  # 64MB cache
            "foreign_keys": "ON",  # Enable foreign key constraints
            "synchronous": "NORMAL",  # Balance between safety and performance
        }
    )


# Initialize database instance
database: Optional[PostgresqlDatabase | SqliteDatabase] = None

# Try to use PostgreSQL first, fallback to SQLite
if should_use_sqlite():
    # Force SQLite usage
    sqlite_path = get_sqlite_path()
    database = create_sqlite_database(sqlite_path)
else:
    # Try PostgreSQL
    db_url = get_database_url()

    if db_url:
        # Use DATABASE_URL if provided
        config = parse_database_url(db_url)
        try:
            database = create_postgresql_database(config)
        except Exception as e:
            print(f"Failed to connect to PostgreSQL: {e}")
            print("Falling back to SQLite...")
            sqlite_path = get_sqlite_path()
            database = create_sqlite_database(sqlite_path)
    else:
        # Try individual environment variables
        config = get_database_config()
        if config["password"]:
            try:
                database = create_postgresql_database(config)
            except Exception as e:
                print(f"Failed to connect to PostgreSQL: {e}")
                print("Falling back to SQLite...")
                sqlite_path = get_sqlite_path()
                database = create_sqlite_database(sqlite_path)
        else:
            # No password provided, use SQLite
            print("No database password provided, using SQLite...")
            sqlite_path = get_sqlite_path()
            database = create_sqlite_database(sqlite_path)


def init_database():
    """
    Initialize database connection.

    Returns:
        The database instance.

    Raises:
        RuntimeError: If database is not configured.
    """
    if database is None:
        raise RuntimeError("Database not configured")

    if database.is_closed():
        database.connect()

    return database


def close_database():
    """Close database connection if open."""
    if database is not None and not database.is_closed():
        database.close()


def get_database():
    """
    Get the database instance.

    Returns:
        The database instance (may not be connected).

    Raises:
        RuntimeError: If database is not configured.
    """
    if database is None:
        raise RuntimeError("Database not configured")

    return database


def is_postgresql() -> bool:
    """Check if the current database is PostgreSQL."""
    return database is not None and isinstance(database, (PostgresqlDatabase, PooledPostgresqlDatabase))


def is_sqlite() -> bool:
    """Check if the current database is SQLite."""
    return database is not None and isinstance(database, SqliteDatabase)


def get_database_info() -> dict:
    """
    Get information about the current database configuration.

    Returns:
        Dictionary with database type and connection info.
    """
    if database is None:
        return {
            "type": "none",
            "configured": False,
        }

    if isinstance(database, SqliteDatabase):
        return {
            "type": "sqlite",
            "configured": True,
            "path": database.database,
        }
    elif isinstance(database, (PostgresqlDatabase, PooledPostgresqlDatabase)):
        return {
            "type": "postgresql",
            "configured": True,
            "database": database.database,
            "host": database.database_kwargs.get("host", "unknown"),
            "port": database.database_kwargs.get("port", 5432),
            "user": database.database_kwargs.get("user", "unknown"),
        }
    else:
        return {
            "type": "unknown",
            "configured": True,
        }


# Auto-initialize on import (optional, can be removed if lazy init preferred)
try:
    init_database()
except Exception as e:
    print(f"Warning: Failed to initialize database: {e}")
    print("Database will be initialized on first use.")
