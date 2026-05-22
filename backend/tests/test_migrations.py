from __future__ import annotations

from pathlib import Path

from job_alert_automation import cli
from job_alert_automation.migrations import MIGRATIONS_DIR, MigrationResult, list_migration_files


def test_migration_sql_files_are_discoverable() -> None:
    files = list_migration_files()

    assert [path.name for path in files] == [
        "001_initial_schema.sql",
        "002_analysis_and_batches.sql",
        "003_auth_profiles.sql",
        "004_gmail_oauth_connections.sql",
        "005_ai_analysis_provider.sql",
        "006_user_documents.sql",
    ]


def test_migration_sql_files_are_ordered(tmp_path: Path) -> None:
    (tmp_path / "002_second.sql").write_text("SELECT 2;", encoding="utf-8")
    (tmp_path / "001_first.sql").write_text("SELECT 1;", encoding="utf-8")

    files = list_migration_files(tmp_path)

    assert [path.name for path in files] == ["001_first.sql", "002_second.sql"]


def test_initial_schema_tracks_schema_migrations() -> None:
    sql = (MIGRATIONS_DIR / "001_initial_schema.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS schema_migrations" in sql
    assert "CREATE UNIQUE INDEX IF NOT EXISTS jobs_source_url_hash_unique" in sql
    assert "CREATE UNIQUE INDEX IF NOT EXISTS jobs_source_fallback_unique" in sql
    assert "WHERE normalized_url_hash IS NOT NULL" in sql
    assert "WHERE normalized_url_hash IS NULL" in sql


def test_analysis_and_batches_migration_exists() -> None:
    sql = (MIGRATIONS_DIR / "002_analysis_and_batches.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS job_run_occurrences" in sql
    assert "seen_as_new boolean NOT NULL DEFAULT false" in sql
    assert "CREATE TABLE IF NOT EXISTS analysis_batches" in sql
    assert "CREATE TABLE IF NOT EXISTS codex_job_analyses" in sql
    assert "first_seen_run_id" in sql
    assert "last_seen_run_id" in sql


def test_auth_profiles_migration_exists() -> None:
    sql = (MIGRATIONS_DIR / "003_auth_profiles.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS app_user_profiles" in sql
    assert "auth_subject text PRIMARY KEY" in sql
    assert "user_id text NOT NULL UNIQUE REFERENCES app_users(id)" in sql


def test_gmail_oauth_connections_migration_exists() -> None:
    sql = (MIGRATIONS_DIR / "004_gmail_oauth_connections.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS gmail_oauth_connections" in sql
    assert "encrypted_credentials text NOT NULL" in sql
    assert "scope text NOT NULL DEFAULT 'https://www.googleapis.com/auth/gmail.readonly'" in sql
    assert "user_id text PRIMARY KEY REFERENCES app_users(id)" in sql


def test_ai_analysis_provider_migration_exists() -> None:
    sql = (MIGRATIONS_DIR / "005_ai_analysis_provider.sql").read_text(encoding="utf-8")

    assert "ADD COLUMN IF NOT EXISTS provider text NOT NULL DEFAULT 'codex'" in sql
    assert "codex_job_analyses_provider_idx" in sql


def test_user_documents_migration_exists() -> None:
    sql = (MIGRATIONS_DIR / "006_user_documents.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS user_documents" in sql
    assert "document_type IN ('profile_markdown', 'resume_pdf', 'cover_letter_template')" in sql
    assert "stored_path text NOT NULL" in sql


def test_migrate_dispatches_manual_migration(monkeypatch) -> None:
    calls: list[str] = []

    monkeypatch.setattr(cli, "get_database_url", lambda required: "postgresql://safe-placeholder")
    monkeypatch.setattr(
        cli,
        "apply_migrations",
        lambda database_url: calls.append(database_url) or MigrationResult(applied=("001_initial_schema",), skipped=()),
    )

    exit_code = cli.main(["--migrate"])

    assert exit_code == 0
    assert calls == ["postgresql://safe-placeholder"]


def test_dry_run_does_not_apply_migrations(monkeypatch) -> None:
    def fail_if_called(_database_url):
        raise AssertionError("dry-run must not apply migrations")

    monkeypatch.setattr(cli, "apply_migrations", fail_if_called)
    monkeypatch.setattr(cli, "build_dry_run_preview", lambda user_id, *, max_results_per_source: None)
    monkeypatch.setattr(cli, "format_dry_run_preview", lambda preview: "dry-run")

    exit_code = cli.main(["--dry-run"])

    assert exit_code == 0


def test_run_now_does_not_apply_migrations(monkeypatch) -> None:
    def fail_if_called(_database_url):
        raise AssertionError("run-now must not apply migrations")

    from job_alert_automation.repository import IngestionPersistSummary

    monkeypatch.setattr(cli, "apply_migrations", fail_if_called)
    monkeypatch.setattr(cli, "get_database_url", lambda required: "postgresql://safe-placeholder")
    monkeypatch.setattr(
        cli,
        "run_ingestion_for_user",
        lambda database_url, *, user_id, max_results_per_source: IngestionPersistSummary(1, 0, 0, 0, 0, 0, 0),
    )

    exit_code = cli.main(["--user", "minjian", "--run-now"])

    assert exit_code == 0


def test_fetch_gmail_does_not_apply_migrations(monkeypatch) -> None:
    def fail_if_called(_database_url):
        raise AssertionError("fetch-gmail must not apply migrations")

    monkeypatch.setattr(cli, "apply_migrations", fail_if_called)
    monkeypatch.setattr(cli, "fetch_recent_alert_metadata", lambda _user_id, *, max_results_per_source: [])

    exit_code = cli.main(["--user", "chang", "--fetch-gmail"])

    assert exit_code == 0


def test_fetch_gmail_with_body_does_not_apply_migrations(monkeypatch) -> None:
    def fail_if_called(_database_url):
        raise AssertionError("fetch-gmail --include-body must not apply migrations")

    monkeypatch.setattr(cli, "apply_migrations", fail_if_called)
    monkeypatch.setattr(cli, "fetch_recent_alert_content", lambda _user_id, *, max_results_per_source: [])

    exit_code = cli.main(["--user", "minjian", "--fetch-gmail", "--include-body"])

    assert exit_code == 0
