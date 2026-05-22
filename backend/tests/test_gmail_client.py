from __future__ import annotations

from datetime import datetime

from job_alert_automation.gmail_client import (
    GMAIL_READONLY_SCOPE,
    GMAIL_SCOPES,
    _parse_header_datetime,
    fetch_alert_content_with_service,
    get_message_content,
    load_gmail_oauth_settings,
)


def test_gmail_scope_is_readonly_only() -> None:
    assert GMAIL_SCOPES == [GMAIL_READONLY_SCOPE]
    assert GMAIL_READONLY_SCOPE == "https://www.googleapis.com/auth/gmail.readonly"


def test_gmail_oauth_settings_use_configured_users() -> None:
    settings = load_gmail_oauth_settings()

    assert "minjian" in settings.token_paths
    assert "chang" in settings.token_paths
    assert settings.client_secrets_file.name.endswith(".json")
    assert settings.token_paths["minjian"].name.endswith(".json")
    assert settings.token_paths["chang"].name.endswith(".json")


def test_parse_header_datetime_handles_valid_date() -> None:
    parsed = _parse_header_datetime("Tue, 20 May 2026 10:00:00 +0200")

    assert isinstance(parsed, datetime)
    assert parsed.year == 2026


def test_parse_header_datetime_handles_invalid_date() -> None:
    assert _parse_header_datetime("not a date") is None


class _FakeExecute:
    def __init__(self, response):
        self.response = response

    def execute(self):
        return self.response


class _FakeMessages:
    def __init__(self, response):
        self.response = response
        self.get_calls = []

    def get(self, **kwargs):
        self.get_calls.append(kwargs)
        return _FakeExecute(self.response)

    def list(self, **kwargs):
        return _FakeExecute({"messages": [{"id": "msg-1"}]})


class _FakeUsers:
    def __init__(self, messages):
        self._messages = messages

    def messages(self):
        return self._messages


class _FakeService:
    def __init__(self, response):
        self.messages_resource = _FakeMessages(response)

    def users(self):
        return _FakeUsers(self.messages_resource)


def test_get_message_content_uses_full_format_and_extracts_safe_metadata() -> None:
    import base64

    encoded_body = base64.urlsafe_b64encode(b"Hello Berlin").decode("ascii").rstrip("=")
    service = _FakeService(
        {
            "id": "msg-1",
            "threadId": "thread-1",
            "snippet": "Hello",
            "payload": {
                "headers": [
                    {"name": "From", "value": "jobs@example.com"},
                    {"name": "Subject", "value": "Job alert"},
                ],
                "mimeType": "text/plain",
                "body": {"data": encoded_body},
            },
        }
    )

    content = get_message_content(service, user_id="minjian", message_id="msg-1", source="linkedin")

    assert service.messages_resource.get_calls == [{"userId": "me", "id": "msg-1", "format": "full"}]
    assert content.metadata.gmail_message_id == "msg-1"
    assert content.metadata.source == "linkedin"
    assert content.metadata.subject == "Job alert"
    assert content.text_body == "Hello Berlin"
    assert content.body_hash


def test_fetch_alert_content_with_service_uses_explicit_web_queries() -> None:
    import base64

    encoded_body = base64.urlsafe_b64encode(b"Title: Werkstudent AI").decode("ascii").rstrip("=")
    service = _FakeService(
        {
            "id": "msg-1",
            "payload": {
                "headers": [],
                "mimeType": "text/plain",
                "body": {"data": encoded_body},
            },
        }
    )

    contents = fetch_alert_content_with_service(
        service,
        user_id="auth_profile_123",
        source_queries={"linkedin": "from:(linkedin) newer_than:7d"},
        max_results_per_source=3,
    )

    assert len(contents) == 1
    assert contents[0].metadata.user_id == "auth_profile_123"
    assert contents[0].metadata.source == "linkedin"
