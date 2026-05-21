from __future__ import annotations

import pytest

from job_alert_automation import cli
from job_alert_automation.config import ConfigError
from job_alert_automation.gmail_client import GmailAuthRequired
from job_alert_automation.models import JobFilterResult, ParsedJob
from job_alert_automation.preview import DryRunPreview


def _preview(user_id: str) -> DryRunPreview:
    return DryRunPreview(
        user_id=user_id,
        fetched_email_count=1,
        parsed_job_count=1,
        unique_job_count=1,
        duplicate_job_count=0,
        likely_relevant_count=1,
        unlikely_relevant_count=0,
        results=(
            JobFilterResult(
                job=ParsedJob(source="linkedin", title="Werkstudent AI", company="Example", location="Berlin"),
                likely_relevant=True,
                relevance_reason="matched role keyword(s): werkstudent ai",
            ),
        ),
    )


def test_help_works(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])

    assert exc_info.value.code == 0
    assert "--dry-run" in capsys.readouterr().out


def test_dry_run_accepts_all_users(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    calls: list[tuple[str, int]] = []

    def fake_preview(user_id: str, *, max_results_per_source: int) -> DryRunPreview:
        calls.append((user_id, max_results_per_source))
        return _preview(user_id)

    monkeypatch.setattr(cli, "build_dry_run_preview", fake_preview)

    exit_code = cli.main(["--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "minjian" in output
    assert "chang" in output
    assert "Dry-run preview" in output
    assert calls == [("minjian", 10), ("chang", 10)]


def test_run_now_dispatches_ingestion(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    from job_alert_automation.repository import IngestionPersistSummary

    monkeypatch.setattr(cli, "get_database_url", lambda required: "postgresql://safe-placeholder")
    monkeypatch.setattr(
        cli,
        "run_ingestion_for_user",
        lambda database_url, *, user_id, max_results_per_source: IngestionPersistSummary(
            ingestion_run_id=7,
            fetched_count=1,
            parsed_count=1,
            unique_count=1,
            new_count=1,
            seen_again_count=0,
            likely_relevant_count=1,
        ),
    )

    exit_code = cli.main(["--user", "minjian", "--run-now"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Run 7 completed for user 'minjian'" in output
    assert "newly discovered: 1" in output


def test_user_minjian_dry_run(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(cli, "build_dry_run_preview", lambda user_id, *, max_results_per_source: _preview(user_id))

    exit_code = cli.main(["--user", "minjian", "--dry-run", "--max-results", "4"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "minjian" in output
    assert "chang" not in output


def test_user_chang_dry_run(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(cli, "build_dry_run_preview", lambda user_id, *, max_results_per_source: _preview(user_id))

    exit_code = cli.main(["--user", "chang", "--dry-run"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "chang" in output
    assert "minjian" not in output


def test_all_user_dry_run_skips_unauthorized_user(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_preview(user_id: str, *, max_results_per_source: int) -> DryRunPreview:
        if user_id == "chang":
            raise GmailAuthRequired("Gmail authorization is required for user 'chang'.")
        return _preview(user_id)

    monkeypatch.setattr(cli, "build_dry_run_preview", fake_preview)

    exit_code = cli.main(["--dry-run"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Dry-run preview for user 'minjian'" in captured.out
    assert "Skipping user 'chang'" in captured.err


def test_selected_user_dry_run_requires_authorization(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        cli,
        "build_dry_run_preview",
        lambda user_id, *, max_results_per_source: (_ for _ in ()).throw(
            GmailAuthRequired("Gmail authorization is required for user 'chang'.")
        ),
    )

    exit_code = cli.main(["--user", "chang", "--dry-run"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Gmail authorization required" in captured.err


def test_invalid_user_exits_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["--user", "unknown", "--dry-run"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Unknown user" in captured.err
    assert "postgres://" not in captured.err
    assert "postgresql://" not in captured.err


def test_check_db_requires_database_url(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def missing_database_url(*, required: bool):
        assert required is True
        raise ConfigError("DATABASE_URL is required for this command. Add it to your local .env file.")

    monkeypatch.setattr(cli, "get_database_url", missing_database_url)

    exit_code = cli.main(["--check-db"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "DATABASE_URL is required" in captured.err
    assert "postgres://" not in captured.err
    assert "postgresql://" not in captured.err


def test_authorize_gmail_requires_single_user(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["--authorize-gmail"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "--authorize-gmail requires --user" in captured.err


def test_fetch_gmail_dispatches_metadata_fetch(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    calls: list[tuple[str, int]] = []

    def fake_fetch(user_id: str, *, max_results_per_source: int):
        calls.append((user_id, max_results_per_source))
        return []

    monkeypatch.setattr(cli, "fetch_recent_alert_metadata", fake_fetch)

    exit_code = cli.main(["--user", "minjian", "--fetch-gmail", "--max-results", "3"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert calls == [("minjian", 3)]
    assert "No email changes" in output


def test_fetch_gmail_with_body_dispatches_content_fetch(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    metadata_calls: list[str] = []
    content_calls: list[tuple[str, int]] = []

    monkeypatch.setattr(
        cli,
        "fetch_recent_alert_metadata",
        lambda user_id, *, max_results_per_source: metadata_calls.append(user_id) or [],
    )
    monkeypatch.setattr(
        cli,
        "fetch_recent_alert_content",
        lambda user_id, *, max_results_per_source: content_calls.append((user_id, max_results_per_source)) or [],
    )

    exit_code = cli.main(["--user", "chang", "--fetch-gmail", "--include-body", "--max-results", "2"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert metadata_calls == []
    assert content_calls == [("chang", 2)]
    assert "Fetched Gmail content" in output


def test_prepare_analysis_dispatches(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    from job_alert_automation.repository import AnalysisBatchRecord

    calls = []
    monkeypatch.setattr(cli, "get_database_url", lambda required: "postgresql://safe-placeholder")
    monkeypatch.setattr(
        cli,
        "prepare_analysis_request",
        lambda database_url, *, user_id, filters: calls.append((user_id, filters.latest_run, filters.new_in_run_only))
        or AnalysisBatchRecord(
            analysis_batch_id=5,
            request_markdown_path="output/analysis_requests/latest_minjian.md",
            request_json_path="output/analysis_requests/latest_minjian.json",
            job_count=2,
        ),
    )

    exit_code = cli.main(["--prepare-analysis", "--user", "minjian", "--latest-run", "--new-in-run-only"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert calls == [("minjian", True, True)]
    assert "Analysis batch id: 5" in output


def test_import_analysis_dispatches(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    from job_alert_automation.repository import AnalysisImportSummary

    calls = []
    monkeypatch.setattr(cli, "get_database_url", lambda required: "postgresql://safe-placeholder")
    monkeypatch.setattr(
        cli,
        "import_analysis_results",
        lambda database_url, *, result_path, overwrite: calls.append((str(result_path), overwrite))
        or AnalysisImportSummary(imported_count=1, skipped_count=0, updated_statuses_count=1),
    )

    exit_code = cli.main(["--import-analysis", "output/analysis_results/latest_minjian_result.json", "--overwrite"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert calls == [("output/analysis_results/latest_minjian_result.json", True)]
    assert "Imported analyses: 1" in output
