from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from job_alert_automation import analysis
from job_alert_automation.analysis import (
    AnalysisFilters,
    AnalysisValidationError,
    import_analysis_results,
    load_profile_content,
    prepare_analysis_request,
    render_analysis_markdown,
)
from job_alert_automation.repository import StoredJob


class _FakeConn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def commit(self):
        return None


def _stored_job(job_id: int = 123, discovery_status: str = "newly discovered in selected run") -> StoredJob:
    now = datetime(2026, 5, 20, tzinfo=timezone.utc)
    return StoredJob(
        job_id=job_id,
        user_id="minjian",
        title="Werkstudent AI Automation",
        company="Example Labs",
        location="Berlin",
        source="linkedin",
        url="https://example.com/job",
        short_description="Build automation workflows.",
        likely_relevant=True,
        matched_keywords=("werkstudent ai",),
        matched_locations=("berlin",),
        current_status="new",
        first_seen_at=now,
        last_seen_at=now,
        first_seen_run_id=7,
        last_seen_run_id=7,
        discovery_status=discovery_status,
    )


def test_missing_profile_file_warns_and_falls_back(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    missing = tmp_path / "profile_minjian.md"
    monkeypatch.setattr(analysis, "profile_path_for_user", lambda user_id: missing)

    profile = load_profile_content("minjian")

    assert profile.warning
    assert "Private profile file not found" in profile.content
    assert "Target role keywords" in profile.content


def test_profile_file_content_is_included(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "profile_minjian.md"
    path.write_text("Private local profile summary", encoding="utf-8")
    monkeypatch.setattr(analysis, "profile_path_for_user", lambda user_id: path)

    profile = load_profile_content("minjian")

    assert profile.warning is None
    assert profile.content == "Private local profile summary"


def test_render_analysis_markdown_contains_scope_schema_and_job_id(tmp_path: Path) -> None:
    profile = analysis.ProfileContent(path=tmp_path / "profile.md", content="Profile summary")
    markdown = render_analysis_markdown(
        user_display_name="Minjian",
        user_id="minjian",
        profile=profile,
        jobs=[_stored_job()],
        filters=AnalysisFilters(latest_run=True, new_in_run_only=True, status="new"),
        resolved_run_id=7,
    )

    assert "# Codex Job Analysis Request" in markdown
    assert "Latest Run / Run ID 7" in markdown
    assert '"priority": "High"' in markdown
    assert "- job_id: 123" in markdown
    assert "newly discovered in selected run" in markdown


def test_prepare_analysis_writes_markdown_and_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(analysis, "ANALYSIS_REQUEST_DIR", tmp_path)
    monkeypatch.setattr(analysis, "connect", lambda database_url: _FakeConn())
    monkeypatch.setattr(analysis, "latest_ingestion_run_id", lambda conn, *, user_id: 7)
    monkeypatch.setattr(analysis, "select_jobs_for_analysis", lambda conn, **kwargs: [_stored_job()])
    monkeypatch.setattr(analysis, "create_analysis_batch", lambda conn, **kwargs: 44)
    monkeypatch.setattr(
        analysis,
        "load_profile_content",
        lambda user_id: analysis.ProfileContent(path=tmp_path / "profile.md", content="Profile summary"),
    )

    record = prepare_analysis_request(
        "postgresql://placeholder",
        user_id="minjian",
        filters=AnalysisFilters(latest_run=True, new_in_run_only=True),
    )

    assert record.analysis_batch_id == 44
    assert record.job_count == 1
    latest_json = tmp_path / "latest_minjian.json"
    assert latest_json.exists()
    payload = json.loads(latest_json.read_text(encoding="utf-8"))
    assert payload["analysis_batch_id"] == 44
    assert payload["jobs"][0]["job_id"] == 123


def test_prepare_analysis_requires_run_scope_for_new_in_run_only() -> None:
    with pytest.raises(Exception) as exc_info:
        prepare_analysis_request(
            "postgresql://placeholder",
            user_id="minjian",
            filters=AnalysisFilters(new_in_run_only=True),
        )

    assert "--new-in-run-only requires --latest-run or --run-id" in str(exc_info.value)


def test_import_analysis_validates_priority(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps({"user_id": "minjian", "results": [{"job_id": 1, "priority": "Urgent"}]}),
        encoding="utf-8",
    )

    with pytest.raises(AnalysisValidationError):
        import_analysis_results("postgresql://placeholder", result_path=path)


def test_import_analysis_validates_suggested_status(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "user_id": "minjian",
                "results": [{"job_id": 1, "priority": "High", "suggested_status": "interviewing"}],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(AnalysisValidationError):
        import_analysis_results("postgresql://placeholder", result_path=path)


def test_import_analysis_inserts_and_updates_status(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    path.write_text(
        json.dumps(
            {
                "analysis_batch_id": 10,
                "user_id": "minjian",
                "results": [
                    {
                        "job_id": 123,
                        "score": 8.5,
                        "priority": "High",
                        "reason": "Strong fit.",
                        "concern": "Check German level.",
                        "suggested_status": "saved",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    calls: list[tuple[str, int | str | None]] = []
    monkeypatch.setattr(analysis, "connect", lambda database_url: _FakeConn())
    monkeypatch.setattr(analysis, "job_exists_for_user", lambda conn, *, user_id, job_id: True)
    monkeypatch.setattr(analysis, "analysis_exists", lambda conn, **kwargs: False)
    monkeypatch.setattr(analysis, "insert_analysis", lambda conn, **kwargs: calls.append(("insert", kwargs["job_id"])))
    monkeypatch.setattr(
        analysis,
        "update_user_job_status",
        lambda conn, **kwargs: calls.append(("status", kwargs["status"])),
    )
    monkeypatch.setattr(
        analysis,
        "mark_analysis_batch_imported",
        lambda conn, **kwargs: calls.append(("batch", kwargs["analysis_batch_id"])),
    )

    summary = import_analysis_results("postgresql://placeholder", result_path=path)

    assert summary.imported_count == 1
    assert summary.skipped_count == 0
    assert summary.updated_statuses_count == 1
    assert calls == [("insert", 123), ("status", "saved"), ("batch", 10)]


def test_import_analysis_skips_duplicate_without_overwrite(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    path.write_text(
        json.dumps({"analysis_batch_id": 10, "user_id": "minjian", "results": [{"job_id": 123, "priority": "Low"}]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(analysis, "connect", lambda database_url: _FakeConn())
    monkeypatch.setattr(analysis, "job_exists_for_user", lambda conn, *, user_id, job_id: True)
    monkeypatch.setattr(analysis, "analysis_exists", lambda conn, **kwargs: True)
    monkeypatch.setattr(analysis, "mark_analysis_batch_imported", lambda conn, **kwargs: None)

    summary = import_analysis_results("postgresql://placeholder", result_path=path, overwrite=False)

    assert summary.imported_count == 0
    assert summary.skipped_count == 1
