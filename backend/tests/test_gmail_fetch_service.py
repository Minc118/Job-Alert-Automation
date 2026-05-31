from __future__ import annotations

import pytest
from fastapi import HTTPException

from api.schemas import UserPreferencesResponse
from api.services import gmail_fetch_service
from job_alert_automation import ingestion
from job_alert_automation.models import EmailMessageContent, EmailMessageMetadata, JobFilterResult, ParsedJob, UserPreferences
from job_alert_automation.repository import IngestionPersistSummary


def test_run_connected_gmail_fetch_uses_connected_credentials_and_returns_summary(monkeypatch) -> None:
    status_updates: list[tuple[str, str, bool]] = []
    fetch_calls: list[tuple[str, dict[str, str], int]] = []

    monkeypatch.setattr(
        gmail_fetch_service,
        "get_preferences",
        lambda user_id: UserPreferencesResponse(
            userId=user_id,
            targetRoleKeywords=["Werkstudent AI"],
            preferredLocations=["Berlin"],
            excludedKeywords=["Senior"],
            sourceQueries={"linkedin": "from:(linkedin) newer_than:7d"},
        ),
    )
    monkeypatch.setattr(gmail_fetch_service, "_load_connected_credentials", lambda _user_id: object())
    monkeypatch.setattr(gmail_fetch_service, "build_gmail_service", lambda _credentials: object())
    monkeypatch.setattr(gmail_fetch_service, "require_database_url", lambda: "postgresql://safe-placeholder")
    monkeypatch.setattr(
        gmail_fetch_service,
        "fetch_alert_content_with_service",
        lambda _service, *, user_id, source_queries, max_results_per_source: fetch_calls.append(
            (user_id, source_queries, max_results_per_source)
        )
        or [EmailMessageContent(metadata=EmailMessageMetadata(user_id=user_id, gmail_message_id="msg-1", source="linkedin"))],
    )

    def fake_run_ingestion(database_url, *, user_id, preferences, fetch_contents, mode):
        assert database_url == "postgresql://safe-placeholder"
        assert user_id == "auth_profile_123"
        assert preferences.target_role_keywords == ("Werkstudent AI",)
        assert mode == "gmail_web_fetch"
        assert len(fetch_contents()) == 1
        return IngestionPersistSummary(
            ingestion_run_id=42,
            fetched_count=1,
            parsed_count=2,
            unique_count=2,
            new_count=1,
            seen_again_count=1,
            likely_relevant_count=2,
            skipped_count=0,
            source_counts={"linkedin": 1},
            warnings=(),
        )

    monkeypatch.setattr(gmail_fetch_service, "run_ingestion_with_fetch", fake_run_ingestion)
    monkeypatch.setattr(
        gmail_fetch_service,
        "_mark_connection_status",
        lambda user_id, *, status_value, encrypted_credentials=None, last_error=None, fetched=False: status_updates.append(
            (user_id, status_value, fetched)
        ),
    )

    summary = gmail_fetch_service.run_connected_gmail_fetch("auth_profile_123", max_results_per_source=7)

    assert summary.run_id == 42
    assert summary.new_job_count == 1
    assert summary.scanned_message_count == 1
    assert summary.parsed_job_count == 2
    assert summary.seen_before_count == 1
    assert summary.skipped_count == 0
    assert summary.source_counts == {"linkedin": 1}
    assert summary.warnings == []
    assert fetch_calls == [("auth_profile_123", {"linkedin": "from:(linkedin) newer_than:7d"}, 7)]
    assert status_updates == [("auth_profile_123", "connected", True)]


def test_connection_credentials_requires_gmail_connection(monkeypatch) -> None:
    class FakeConnection:
        def __enter__(self) -> "FakeConnection":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def execute(self, query: str, params: object) -> "FakeConnection":
            return self

        def fetchone(self) -> None:
            return None

    monkeypatch.setattr(gmail_fetch_service, "readonly_connection", FakeConnection)

    with pytest.raises(HTTPException) as exc_info:
        gmail_fetch_service._connection_credentials("auth_profile_123")

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == gmail_fetch_service.SAFE_GMAIL_NOT_CONNECTED_ERROR


def test_run_connected_gmail_fetch_returns_empty_safe_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        gmail_fetch_service,
        "get_preferences",
        lambda user_id: UserPreferencesResponse(
            userId=user_id,
            targetRoleKeywords=[],
            preferredLocations=[],
            excludedKeywords=[],
            sourceQueries={"LinkedIn": "from:(linkedin) newer_than:7d", "Indeed": "from:(indeed) newer_than:7d"},
        ),
    )
    monkeypatch.setattr(gmail_fetch_service, "_load_connected_credentials", lambda _user_id: object())
    monkeypatch.setattr(gmail_fetch_service, "build_gmail_service", lambda _credentials: object())
    monkeypatch.setattr(gmail_fetch_service, "require_database_url", lambda: "postgresql://safe-placeholder")
    monkeypatch.setattr(gmail_fetch_service, "fetch_alert_content_with_service", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        gmail_fetch_service,
        "run_ingestion_with_fetch",
        lambda database_url, *, user_id, preferences, fetch_contents, mode: IngestionPersistSummary(
            ingestion_run_id=43,
            fetched_count=0,
            parsed_count=0,
            unique_count=0,
            new_count=0,
            seen_again_count=0,
            likely_relevant_count=0,
            skipped_count=0,
            source_counts={},
            warnings=(),
        ),
    )
    monkeypatch.setattr(gmail_fetch_service, "_mark_connection_status", lambda *args, **kwargs: None)

    summary = gmail_fetch_service.run_connected_gmail_fetch("auth_profile_123")

    assert summary.run_id == 43
    assert summary.scanned_message_count == 0
    assert summary.source_counts == {"LinkedIn": 0, "Indeed": 0}
    assert summary.warnings == [gmail_fetch_service.SAFE_GMAIL_EMPTY_RESULT_WARNING]
    assert "body" not in summary.model_dump_json().lower()


def test_load_connected_credentials_marks_invalid_token_for_reconnect(monkeypatch) -> None:
    status_updates: list[tuple[str, str]] = []

    class FakeCredentials:
        expired = False
        refresh_token = None
        valid = False

        @classmethod
        def from_authorized_user_info(cls, info, scopes):
            return cls()

    monkeypatch.setattr(gmail_fetch_service, "_connection_credentials", lambda user_id: "{}")
    monkeypatch.setattr(gmail_fetch_service, "_import_credentials_modules", lambda: (object, FakeCredentials))
    monkeypatch.setattr(
        gmail_fetch_service,
        "_mark_connection_status",
        lambda user_id, *, status_value, encrypted_credentials=None, last_error=None, fetched=False: status_updates.append((user_id, status_value)),
    )

    with pytest.raises(HTTPException) as exc_info:
        gmail_fetch_service._load_connected_credentials("auth_profile_123")

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == gmail_fetch_service.SAFE_GMAIL_RECONNECT_ERROR
    assert status_updates == [("auth_profile_123", "token_expired")]


def test_ingestion_skips_parser_failure_and_persists_run(monkeypatch) -> None:
    content_ok = EmailMessageContent(metadata=EmailMessageMetadata(user_id="auth_profile_123", gmail_message_id="msg-ok", source="LinkedIn"))
    content_bad = EmailMessageContent(metadata=EmailMessageMetadata(user_id="auth_profile_123", gmail_message_id="msg-bad", source="LinkedIn"))
    parsed_job = ParsedJob(source="LinkedIn", title="Working Student AI", company="Example Co", location="Berlin", url="https://example.test/job")
    completed: list[IngestionPersistSummary] = []
    persisted_messages: list[str] = []

    class FakeConnection:
        def __enter__(self) -> "FakeConnection":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def commit(self) -> None:
            return None

    def fake_parse(content: EmailMessageContent) -> list[ParsedJob]:
        if content.metadata.gmail_message_id == "msg-bad":
            raise ValueError("parser failed")
        return [parsed_job]

    monkeypatch.setattr(ingestion, "connect", lambda database_url: FakeConnection())
    monkeypatch.setattr(ingestion, "create_ingestion_run", lambda conn, *, selected_user_id, mode: 44)
    monkeypatch.setattr(ingestion, "parse_email_content", fake_parse)
    monkeypatch.setattr(ingestion, "dedupe_jobs", lambda jobs: (jobs, object()))
    monkeypatch.setattr(
        ingestion,
        "evaluate_jobs_relevance",
        lambda jobs, preferences: [JobFilterResult(job=job, likely_relevant=True, matched_keywords=("AI",)) for job in jobs],
    )
    monkeypatch.setattr(ingestion, "upsert_email_message", lambda conn, *, content: persisted_messages.append(content.metadata.gmail_message_id))
    monkeypatch.setattr(ingestion, "upsert_job", lambda conn, *, job: 101)
    monkeypatch.setattr(ingestion, "upsert_user_job", lambda conn, **kwargs: True)
    monkeypatch.setattr(ingestion, "complete_ingestion_run", lambda conn, *, ingestion_run_id, summary, status="completed": completed.append(summary))

    summary = ingestion.run_ingestion_with_fetch(
        "postgresql://safe-placeholder",
        user_id="auth_profile_123",
        preferences=UserPreferences(user_id="auth_profile_123", target_role_keywords=("AI",)),
        fetch_contents=lambda: [content_ok, content_bad],
        mode="gmail_web_fetch",
    )

    assert summary.ingestion_run_id == 44
    assert summary.fetched_count == 2
    assert summary.parsed_count == 1
    assert summary.new_count == 1
    assert summary.skipped_count == 1
    assert summary.source_counts == {"LinkedIn": 2}
    assert summary.warnings == ("Skipped 1 message(s) because parsing failed.",)
    assert persisted_messages == ["msg-ok", "msg-bad"]
    assert completed == [summary]


def test_ingestion_counts_duplicate_jobs_as_skipped(monkeypatch) -> None:
    content = EmailMessageContent(metadata=EmailMessageMetadata(user_id="auth_profile_123", gmail_message_id="msg-1", source="Indeed"))
    job_a = ParsedJob(source="Indeed", title="Project Coordinator", company="Example Co", location="Berlin", url="https://example.test/job")
    job_b = ParsedJob(source="Indeed", title="Project Coordinator", company="Example Co", location="Berlin", url="https://example.test/job")

    class FakeConnection:
        def __enter__(self) -> "FakeConnection":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def commit(self) -> None:
            return None

    monkeypatch.setattr(ingestion, "connect", lambda database_url: FakeConnection())
    monkeypatch.setattr(ingestion, "create_ingestion_run", lambda conn, *, selected_user_id, mode: 45)
    monkeypatch.setattr(ingestion, "parse_email_content", lambda _content: [job_a, job_b])
    monkeypatch.setattr(ingestion, "dedupe_jobs", lambda jobs: ([jobs[0]], object()))
    monkeypatch.setattr(
        ingestion,
        "evaluate_jobs_relevance",
        lambda jobs, preferences: [JobFilterResult(job=job, likely_relevant=False) for job in jobs],
    )
    monkeypatch.setattr(ingestion, "upsert_email_message", lambda conn, *, content: None)
    monkeypatch.setattr(ingestion, "upsert_job", lambda conn, *, job: 201)
    monkeypatch.setattr(ingestion, "upsert_user_job", lambda conn, **kwargs: False)
    monkeypatch.setattr(ingestion, "complete_ingestion_run", lambda conn, *, ingestion_run_id, summary, status="completed": None)

    summary = ingestion.run_ingestion_with_fetch(
        "postgresql://safe-placeholder",
        user_id="auth_profile_123",
        preferences=UserPreferences(user_id="auth_profile_123"),
        fetch_contents=lambda: [content],
        mode="gmail_web_fetch",
    )

    assert summary.parsed_count == 2
    assert summary.unique_count == 1
    assert summary.new_count == 0
    assert summary.seen_again_count == 1
    assert summary.skipped_count == 1
    assert summary.source_counts == {"Indeed": 1}
    assert summary.warnings == ("Skipped 1 duplicate job(s).",)
