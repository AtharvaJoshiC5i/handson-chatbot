from collections.abc import Generator
from pathlib import Path
import sqlite3

from app.config.settings import get_settings


class DatabaseConnectionError(Exception):
    """Raised when a SQLite connection cannot be established."""


def get_database_path() -> Path:
    """
    Return the configured SQLite database path.

    Relative paths are resolved from the backend directory.
    Absolute paths are used as-is.
    """

    configured_path = Path(get_settings().database_path)

    if configured_path.is_absolute():
        return configured_path

    backend_root = Path(__file__).resolve().parents[2]
    return backend_root / configured_path


def create_connection() -> sqlite3.Connection:
    """
    Create and configure a SQLite connection.

    Configuration applied to every connection:
    - Row factory for dictionary-like row access
    - Foreign-key enforcement
    - Busy timeout
    """

    database_path = get_database_path()

    try:
        database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        connection = sqlite3.connect(
            database_path,
            timeout=10.0,
        )

        connection.row_factory = sqlite3.Row

        # SQLite foreign-key enforcement is disabled by default.
        connection.execute("PRAGMA foreign_keys = ON;")

        # Wait briefly instead of immediately failing if the database
        # is temporarily locked.
        connection.execute("PRAGMA busy_timeout = 10000;")

        return connection

    except sqlite3.Error as exc:
        raise DatabaseConnectionError(
            f"Unable to connect to SQLite database: {database_path}"
        ) from exc


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """
    FastAPI-compatible database dependency.

    A fresh connection is created for each request and closed after
    the request finishes.
    """

    connection = create_connection()

    try:
        yield connection
    finally:
        connection.close()