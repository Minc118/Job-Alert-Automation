from __future__ import annotations

import pytest
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
