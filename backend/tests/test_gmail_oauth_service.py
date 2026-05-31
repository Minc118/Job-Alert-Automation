from __future__ import annotations

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException

from api.services import gmail_oauth_service


def test_gmail_oauth_state_round_trips_for_expected_user(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GMAIL_OAUTH_STATE_SECRET", "local-test-state-secret")

    state_value = gmail_oauth_service.create_signed_state("auth_profile_123", issued_at=100)
    monkeypatch.setattr(gmail_oauth_service.time, "time", lambda: 120)

    state = gmail_oauth_service.verify_signed_state(state_value)

    assert state.user_id == "auth_profile_123"
    assert state.issued_at == 100


def test_gmail_oauth_state_rejects_tampering(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GMAIL_OAUTH_STATE_SECRET", "local-test-state-secret")
    state_value = gmail_oauth_service.create_signed_state("auth_profile_123", issued_at=100)

    with pytest.raises(HTTPException) as exc_info:
        gmail_oauth_service.verify_signed_state(f"{state_value}tampered")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == gmail_oauth_service.SAFE_GMAIL_STATE_ERROR


def test_gmail_oauth_state_rejects_expired_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GMAIL_OAUTH_STATE_SECRET", "local-test-state-secret")
    state_value = gmail_oauth_service.create_signed_state("auth_profile_123", issued_at=100)
    monkeypatch.setattr(gmail_oauth_service.time, "time", lambda: 100 + gmail_oauth_service.STATE_MAX_AGE_SECONDS + 1)

    with pytest.raises(HTTPException) as exc_info:
        gmail_oauth_service.verify_signed_state(state_value)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == gmail_oauth_service.SAFE_GMAIL_STATE_ERROR


def test_gmail_oauth_state_round_trips_code_verifier(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GMAIL_OAUTH_STATE_SECRET", "local-test-state-secret")
    monkeypatch.setenv("GMAIL_TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))

    state_value = gmail_oauth_service.create_signed_state("auth_profile_123", issued_at=100, code_verifier="a" * 64)
    monkeypatch.setattr(gmail_oauth_service.time, "time", lambda: 120)

    state = gmail_oauth_service.verify_signed_state(state_value)

    assert state.user_id == "auth_profile_123"
    assert state.issued_at == 100
    assert state.code_verifier == "a" * 64


def test_create_authorization_url_reuses_code_verifier_in_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GMAIL_OAUTH_STATE_SECRET", "local-test-state-secret")
    monkeypatch.setenv("GMAIL_TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))
    monkeypatch.setattr(gmail_oauth_service, "_new_code_verifier", lambda: "b" * 64)

    class FakeFlow:
        def __init__(self, state_value: str, code_verifier: str) -> None:
            self.state_value = state_value
            self.code_verifier = code_verifier

        def authorization_url(self, **kwargs: str) -> tuple[str, str]:
            state = gmail_oauth_service.verify_signed_state(self.state_value)
            assert state.code_verifier == self.code_verifier
            assert kwargs["access_type"] == "offline"
            assert kwargs["include_granted_scopes"] == "true"
            assert kwargs["prompt"] == "consent"
            return "https://accounts.google.test/oauth", self.state_value

    def fake_load_web_flow(*, state_value: str | None = None, code_verifier: str | None = None) -> FakeFlow:
        assert state_value is not None
        assert code_verifier == "b" * 64
        return FakeFlow(state_value, code_verifier)

    monkeypatch.setattr(gmail_oauth_service, "_load_web_flow", fake_load_web_flow)

    assert gmail_oauth_service.create_authorization_url("auth_profile_123") == "https://accounts.google.test/oauth"


def test_complete_callback_uses_state_code_verifier_for_token_exchange(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GMAIL_OAUTH_STATE_SECRET", "local-test-state-secret")
    monkeypatch.setenv("GMAIL_TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))
    state_value = gmail_oauth_service.create_signed_state("auth_profile_123", issued_at=100, code_verifier="c" * 64)
    monkeypatch.setattr(gmail_oauth_service.time, "time", lambda: 120)
    captured: dict[str, object] = {}

    class FakeCredentials:
        def to_json(self) -> str:
            return "{}"

    class FakeFlow:
        redirect_uri = "http://localhost:8000/api/gmail/callback"
        credentials = FakeCredentials()

        def __init__(self, code_verifier: str | None) -> None:
            captured["code_verifier"] = code_verifier

        def fetch_token(self, *, code: str) -> None:
            captured["code"] = code

    def fake_load_web_flow(*, state_value: str | None = None, code_verifier: str | None = None) -> FakeFlow:
        assert state_value is not None
        return FakeFlow(code_verifier)

    class FakeConnection:
        def __enter__(self) -> "FakeConnection":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def execute(self, query: str, params: object) -> None:
            captured["database_write"] = True

        def commit(self) -> None:
            captured["database_commit"] = True

    monkeypatch.setattr(gmail_oauth_service, "_load_web_flow", fake_load_web_flow)
    monkeypatch.setattr(gmail_oauth_service, "encrypt_credentials", lambda credentials_json: "encrypted")
    monkeypatch.setattr(gmail_oauth_service, "_gmail_profile_email", lambda credentials: "demo.alex@example.com")
    monkeypatch.setattr(gmail_oauth_service, "write_connection", FakeConnection)
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173")

    redirect = gmail_oauth_service.complete_callback(state_value=state_value, code="auth-code")

    assert redirect == "http://localhost:5173/app/settings?gmail=connected"
    assert captured["code_verifier"] == "c" * 64
    assert captured["code"] == "auth-code"
    assert captured["database_write"] is True
    assert captured["database_commit"] is True
