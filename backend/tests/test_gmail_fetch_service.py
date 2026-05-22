from __future__ import annotations

from api.schemas import UserPreferencesResponse
from api.services import gmail_fetch_service
from job_alert_automation.models import EmailMessageContent, EmailMessageMetadata
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

    assert summary.ingestionRunId == 42
    assert summary.newlyDiscovered == 1
    assert fetch_calls == [("auth_profile_123", {"linkedin": "from:(linkedin) newer_than:7d"}, 7)]
    assert status_updates == [("auth_profile_123", "connected", True)]
