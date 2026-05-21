from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from fastapi import HTTPException, status

from job_alert_automation.config import ConfigError, get_database_url
from job_alert_automation.database import DatabaseError, connect


SAFE_DATABASE_ERROR = "Database is not configured. Add DATABASE_URL to the local .env file."


def require_database_url() -> str:
    try:
        return get_database_url(required=True)
    except ConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_DATABASE_ERROR) from exc


@contextmanager
def database_connection(*, autocommit: bool) -> Iterator[Any]:
    database_url = require_database_url()
    try:
        with connect(database_url, autocommit=autocommit) as conn:
            yield conn
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed. Check local configuration and network access.",
        ) from exc


def readonly_connection() -> Iterator[Any]:
    return database_connection(autocommit=True)


def write_connection() -> Iterator[Any]:
    return database_connection(autocommit=False)
