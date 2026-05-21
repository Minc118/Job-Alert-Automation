from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from .config import ConfigError, REPO_ROOT, get_env_value, load_users_config
from .email_content import body_hash, extract_bodies_from_gmail_message, preferred_text_body
from .models import EmailMessageContent, EmailMessageMetadata


GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_SCOPES = [GMAIL_READONLY_SCOPE]
METADATA_HEADERS = ["From", "Subject", "Date", "To"]


class GmailClientError(RuntimeError):
    """Raised for safe, user-facing Gmail integration errors."""


class GmailAuthRequired(GmailClientError):
    """Raised when a user must authorize Gmail access before fetching."""


@dataclass(frozen=True)
class GmailOAuthSettings:
    client_secrets_file: Path
    token_paths: dict[str, Path]

    def token_path_for(self, user_id: str) -> Path:
        try:
            return self.token_paths[user_id]
        except KeyError as exc:
            raise ConfigError(f"No Gmail token path is configured for user '{user_id}'.") from exc


def _resolve_project_path(value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def load_gmail_oauth_settings() -> GmailOAuthSettings:
    config = load_users_config()
    client_secrets = get_env_value(
        "GOOGLE_OAUTH_CLIENT_SECRETS_FILE",
        default="secrets/google_oauth_client.json",
    )
    token_paths = {
        user_id: _resolve_project_path(
            get_env_value(f"GOOGLE_TOKEN_{user_id.upper()}", default=f"secrets/token_{user_id}.json")
        )
        for user_id in config.users
    }
    return GmailOAuthSettings(
        client_secrets_file=_resolve_project_path(client_secrets),
        token_paths=token_paths,
    )


def _import_google_auth_modules() -> tuple[Any, Any, Any, Any]:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise GmailClientError("Gmail API dependencies are not installed. Reinstall project dependencies.") from exc
    return Request, Credentials, InstalledAppFlow, build


def authorize_gmail_user(user_id: str) -> Path:
    config = load_users_config()
    config.validate_user_id(user_id)
    settings = load_gmail_oauth_settings()

    if not settings.client_secrets_file.exists():
        raise ConfigError("Gmail OAuth client secrets file is missing. Place it under secrets/ and update .env.")

    _, _, InstalledAppFlow, _ = _import_google_auth_modules()
    flow = InstalledAppFlow.from_client_secrets_file(str(settings.client_secrets_file), GMAIL_SCOPES)
    credentials = flow.run_local_server(port=0)

    token_path = settings.token_path_for(user_id)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    return token_path


def load_authorized_credentials(user_id: str) -> Any:
    config = load_users_config()
    config.validate_user_id(user_id)
    settings = load_gmail_oauth_settings()
    token_path = settings.token_path_for(user_id)

    if not token_path.exists():
        raise GmailAuthRequired(f"Gmail authorization is required for user '{user_id}'.")

    Request, Credentials, _, _ = _import_google_auth_modules()
    credentials = Credentials.from_authorized_user_file(str(token_path), GMAIL_SCOPES)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_path.write_text(credentials.to_json(), encoding="utf-8")

    if not credentials or not credentials.valid:
        raise GmailAuthRequired(f"Gmail authorization is required for user '{user_id}'.")

    return credentials


def build_gmail_service(credentials: Any) -> Any:
    _, _, _, build = _import_google_auth_modules()
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def _header_value(message: dict[str, Any], name: str) -> str | None:
    payload = message.get("payload") or {}
    headers = payload.get("headers") or []
    for header in headers:
        if str(header.get("name", "")).lower() == name.lower():
            value = header.get("value")
            return str(value) if value is not None else None
    return None


def _parse_header_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None


def list_message_ids(service: Any, *, query: str, max_results: int) -> list[dict[str, str]]:
    response = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    messages = response.get("messages") or []
    return [message for message in messages if message.get("id")]


def _metadata_from_message(
    message: dict[str, Any],
    *,
    user_id: str,
    message_id: str,
    source: str,
    body_hash_value: str | None = None,
) -> EmailMessageMetadata:
    return EmailMessageMetadata(
        user_id=user_id,
        gmail_message_id=str(message.get("id") or message_id),
        gmail_thread_id=message.get("threadId"),
        source=source,
        sender=_header_value(message, "From"),
        subject=_header_value(message, "Subject"),
        received_at=_parse_header_datetime(_header_value(message, "Date")),
        snippet=message.get("snippet"),
        body_hash=body_hash_value,
    )


def get_message_metadata(service: Any, *, user_id: str, message_id: str, source: str) -> EmailMessageMetadata:
    message = (
        service.users()
        .messages()
        .get(
            userId="me",
            id=message_id,
            format="metadata",
            metadataHeaders=METADATA_HEADERS,
        )
        .execute()
    )
    return _metadata_from_message(message, user_id=user_id, message_id=message_id, source=source)


def get_message_content(service: Any, *, user_id: str, message_id: str, source: str) -> EmailMessageContent:
    message = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )
    text_body, html_body = extract_bodies_from_gmail_message(message)
    preferred_body = preferred_text_body(text_body, html_body)
    body_hash_value = body_hash(preferred_body)
    metadata = _metadata_from_message(
        message,
        user_id=user_id,
        message_id=message_id,
        source=source,
        body_hash_value=body_hash_value,
    )
    return EmailMessageContent(
        metadata=metadata,
        text_body=preferred_body,
        html_body=html_body,
        body_hash=body_hash_value,
    )


def fetch_recent_alert_metadata(
    user_id: str,
    *,
    max_results_per_source: int = 10,
) -> list[EmailMessageMetadata]:
    config = load_users_config()
    config.validate_user_id(user_id)
    preferences = config.preferences[user_id]
    credentials = load_authorized_credentials(user_id)
    service = build_gmail_service(credentials)

    messages: list[EmailMessageMetadata] = []
    for source, query in preferences.source_queries.items():
        for listed_message in list_message_ids(service, query=query, max_results=max_results_per_source):
            messages.append(
                get_message_metadata(
                    service,
                    user_id=user_id,
                    message_id=listed_message["id"],
                    source=source,
                )
            )
    return messages


def fetch_recent_alert_content(
    user_id: str,
    *,
    max_results_per_source: int = 10,
) -> list[EmailMessageContent]:
    config = load_users_config()
    config.validate_user_id(user_id)
    preferences = config.preferences[user_id]
    credentials = load_authorized_credentials(user_id)
    service = build_gmail_service(credentials)

    messages: list[EmailMessageContent] = []
    for source, query in preferences.source_queries.items():
        for listed_message in list_message_ids(service, query=query, max_results=max_results_per_source):
            messages.append(
                get_message_content(
                    service,
                    user_id=user_id,
                    message_id=listed_message["id"],
                    source=source,
                )
            )
    return messages
