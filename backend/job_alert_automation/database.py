from __future__ import annotations

from typing import Any


class DatabaseError(RuntimeError):
    """Raised for safe, user-facing database errors."""


def connect(database_url: str, *, autocommit: bool = False) -> Any:
    try:
        import psycopg
    except ImportError as exc:
        raise DatabaseError("Database dependency is not installed. Run project dependency installation first.") from exc

    try:
        return psycopg.connect(database_url, autocommit=autocommit)
    except Exception as exc:  # pragma: no cover - exercised only with a real database/network
        raise DatabaseError("Could not connect to the database. Check local DATABASE_URL and network access.") from exc


def check_connection(database_url: str) -> None:
    try:
        with connect(database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
    except DatabaseError:
        raise
    except Exception as exc:  # pragma: no cover - exercised only with a real database/network
        raise DatabaseError("Database check failed. Check local DATABASE_URL and network access.") from exc
