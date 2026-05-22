from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status

from api.schemas import GmailConnectionStatusResponse
from api.services.database import readonly_connection, write_connection
from job_alert_automation.config import ConfigError, get_env_value
from job_alert_automation.gmail_client import GMAIL_READONLY_SCOPE, GMAIL_SCOPES, build_gmail_service, load_gmail_oauth_settings


DETECTED_SOURCES = ["LinkedIn", "StepStone", "Indeed"]
STATE_MAX_AGE_SECONDS = 10 * 60
SAFE_GMAIL_CONFIG_ERROR = "Gmail web OAuth is not configured. Add the required Gmail OAuth settings to the local .env file."
SAFE_GMAIL_STATE_ERROR = "Gmail connection state is invalid or expired. Start the connection again."
SAFE_GMAIL_CALLBACK_ERROR = "Gmail connection could not be completed. Start the connection again."


@dataclass(frozen=True)
class GmailOAuthState:
    user_id: str
    issued_at: int


def _urlsafe_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _urlsafe_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))


def _required_env(name: str) -> str:
    try:
        return get_env_value(name)
    except ConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_GMAIL_CONFIG_ERROR) from exc


def _state_secret() -> bytes:
    return _required_env("GMAIL_OAUTH_STATE_SECRET").encode("utf-8")


def _fernet() -> Fernet:
    try:
        return Fernet(_required_env("GMAIL_TOKEN_ENCRYPTION_KEY").encode("utf-8"))
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_GMAIL_CONFIG_ERROR) from exc


def get_redirect_uri() -> str:
    try:
        return get_env_value("GMAIL_OAUTH_REDIRECT_URI", default="http://127.0.0.1:8000/api/gmail/callback")
    except ConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_GMAIL_CONFIG_ERROR) from exc


def _frontend_settings_redirect(outcome: str) -> str:
    frontend_base_url = get_env_value("FRONTEND_BASE_URL", default="http://127.0.0.1:5173").rstrip("/")
    return f"{frontend_base_url}/app/settings?{urlencode({'gmail': outcome})}"


def create_signed_state(user_id: str, *, issued_at: int | None = None) -> str:
    payload = {
        "user_id": user_id,
        "iat": int(issued_at or time.time()),
    }
    encoded_payload = _urlsafe_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signature = hmac.new(_state_secret(), encoded_payload.encode("ascii"), hashlib.sha256).digest()
    return f"{encoded_payload}.{_urlsafe_encode(signature)}"


def verify_signed_state(state_value: str) -> GmailOAuthState:
    try:
        encoded_payload, encoded_signature = state_value.split(".", maxsplit=1)
        expected_signature = hmac.new(_state_secret(), encoded_payload.encode("ascii"), hashlib.sha256).digest()
        supplied_signature = _urlsafe_decode(encoded_signature)
        if not hmac.compare_digest(expected_signature, supplied_signature):
            raise ValueError("Invalid signature.")
        payload = json.loads(_urlsafe_decode(encoded_payload))
        user_id = payload["user_id"]
        issued_at = int(payload["iat"])
        now = int(time.time())
        if not isinstance(user_id, str) or not user_id.strip() or issued_at > now + 60 or now - issued_at > STATE_MAX_AGE_SECONDS:
            raise ValueError("Invalid state claims.")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SAFE_GMAIL_STATE_ERROR) from exc
    return GmailOAuthState(user_id=user_id, issued_at=issued_at)


def _load_web_flow(*, state_value: str | None = None) -> Any:
    settings = load_gmail_oauth_settings()
    if not settings.client_secrets_file.exists():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_GMAIL_CONFIG_ERROR)
    try:
        from google_auth_oauthlib.flow import Flow
    except ImportError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_GMAIL_CONFIG_ERROR) from exc

    flow = Flow.from_client_secrets_file(str(settings.client_secrets_file), scopes=GMAIL_SCOPES, state=state_value)
    flow.redirect_uri = get_redirect_uri()
    return flow


def create_authorization_url(user_id: str) -> str:
    state_value = create_signed_state(user_id)
    flow = _load_web_flow(state_value=state_value)
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return authorization_url


def encrypt_credentials(credentials_json: str) -> str:
    return _fernet().encrypt(credentials_json.encode("utf-8")).decode("ascii")


def decrypt_credentials(encrypted_credentials: str) -> str:
    try:
        return _fernet().decrypt(encrypted_credentials.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stored Gmail authorization could not be read.") from exc


def _gmail_profile_email(credentials: Any) -> str | None:
    try:
        profile = build_gmail_service(credentials).users().getProfile(userId="me").execute()
    except Exception:
        return None
    email = profile.get("emailAddress")
    return str(email) if email else None


def complete_callback(*, state_value: str, code: str) -> str:
    oauth_state = verify_signed_state(state_value)
    flow = _load_web_flow(state_value=state_value)
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
        encrypted_credentials = encrypt_credentials(credentials.to_json())
        connected_email = _gmail_profile_email(credentials)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=SAFE_GMAIL_CALLBACK_ERROR) from exc

    with write_connection() as conn:
        conn.execute(
            """
            INSERT INTO gmail_oauth_connections (
                user_id,
                connected_email,
                encrypted_credentials,
                scope,
                status,
                last_error
            )
            VALUES (%s, %s, %s, %s, 'connected', NULL)
            ON CONFLICT (user_id) DO UPDATE
            SET connected_email = EXCLUDED.connected_email,
                encrypted_credentials = EXCLUDED.encrypted_credentials,
                scope = EXCLUDED.scope,
                status = 'connected',
                last_error = NULL,
                updated_at = now()
            """,
            (oauth_state.user_id, connected_email, encrypted_credentials, GMAIL_READONLY_SCOPE),
        )
        conn.commit()
    return _frontend_settings_redirect("connected")


def get_connection_status(user_id: str) -> GmailConnectionStatusResponse:
    with readonly_connection() as conn:
        row = conn.execute(
            """
            SELECT status, connected_email, last_fetch_at, scope
            FROM gmail_oauth_connections
            WHERE user_id = %s
            """,
            (user_id,),
        ).fetchone()
    if row is None:
        return GmailConnectionStatusResponse(
            status="not_connected",
            connectedEmail=None,
            lastFetchAt=None,
            scope=GMAIL_READONLY_SCOPE,
            detectedSources=DETECTED_SOURCES,
        )
    last_fetch_at = row[2].isoformat(sep=" ", timespec="minutes") if row[2] is not None else None
    return GmailConnectionStatusResponse(
        status=str(row[0]),
        connectedEmail=row[1],
        lastFetchAt=last_fetch_at,
        scope=str(row[3]),
        detectedSources=DETECTED_SOURCES,
    )


def disconnect_gmail(user_id: str) -> GmailConnectionStatusResponse:
    with write_connection() as conn:
        conn.execute("DELETE FROM gmail_oauth_connections WHERE user_id = %s", (user_id,))
        conn.commit()
    return get_connection_status(user_id)
