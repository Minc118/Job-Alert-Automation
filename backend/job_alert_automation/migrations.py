from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import BACKEND_ROOT
from .database import connect


MIGRATIONS_DIR = BACKEND_ROOT / "migrations"


@dataclass(frozen=True)
class MigrationResult:
    applied: tuple[str, ...]
    skipped: tuple[str, ...]


def list_migration_files(migrations_dir: Path = MIGRATIONS_DIR) -> list[Path]:
    if not migrations_dir.exists():
        return []
    return sorted(path for path in migrations_dir.glob("*.sql") if path.is_file())


def migration_version(path: Path) -> str:
    return path.stem


def _ensure_schema_migrations(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version text PRIMARY KEY,
            applied_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )


def _applied_versions(conn) -> set[str]:
    rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
    return {row[0] for row in rows}


def apply_migrations(database_url: str, migrations_dir: Path = MIGRATIONS_DIR) -> MigrationResult:
    migration_files = list_migration_files(migrations_dir)
    applied: list[str] = []
    skipped: list[str] = []

    with connect(database_url, autocommit=True) as conn:
        _ensure_schema_migrations(conn)
        existing_versions = _applied_versions(conn)

        for path in migration_files:
            version = migration_version(path)
            if version in existing_versions:
                skipped.append(version)
                continue

            sql = path.read_text(encoding="utf-8")
            with conn.transaction():
                conn.execute(sql)
                conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (version,))
            applied.append(version)

    return MigrationResult(applied=tuple(applied), skipped=tuple(skipped))
