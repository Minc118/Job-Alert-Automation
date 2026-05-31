from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status

from api.schemas import GmailFetchResponse, UserPreferencesResponse
from api.services.database import readonly_connection, require_database_url, write_connection
from api.services.gmail_oauth_service import decrypt_credentials, encrypt_credentials
from api.services.preference_service import get_preferences
from job_alert_automation.config import ConfigError, load_users_config
from job_alert_automation.gmail_client import GMAIL_SCOPES, build_gmail_service, fetch_alert_content_with_service
from job_alert_automation.ingestion import run_ingestion_with_fetch
from job_alert_automation.models import UserPreferences


SAFE_GMAIL_NOT_CONNECTED_ERROR = "Connect Gmail before fetching job alerts."
SAFE_GMAIL_RECONNECT_ERROR = "Gmail authorization needs to be reconnected before fetching job alerts."
SAFE_GMAIL_FETCH_ERROR = "Gmail fetch failed. Reconnect Gmail or try again later."
SAFE_GMAIL_QUERY_ERROR = "Gmail source queries are not configured for job alert fetching."
SAFE_GMAIL_EMPTY_RESULT_WARNING = "No job alert emails were found for the configured sources."


def _connection_credentials(user_id: str) -> str:
    with readonly_connection() as conn:
        row = conn.execute(
            """
            SELECT encrypted_credentials
            FROM gmail_oauth_connections
            WHERE user_id = %s
            """,
            (user_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=SAFE_GMAIL_NOT_CONNECTED_ERROR)
    return decrypt_credentials(str(row[0]))


def _source_counts_for_response(source_queries: dict[str, str], source_counts: dict[str, int]) -> dict[str, int]:
    return {source: int(source_counts.get(source, 0)) for source in source_queries}


def _mark_connection_status(
    user_id: str,
    *,
    status_value: str,
    encrypted_credentials: str | None = None,
    last_error: str | None = None,
    fetched: bool = False,
) -> None:
    assignments = [
        "status = %s",
        "last_error = %s",
        "updated_at = now()",
    ]
    params: list[Any] = [status_value, last_error[:1000] if last_error else None]
    if encrypted_credentials is not None:
        assignments.append("encrypted_credentials = %s")
        params.append(encrypted_credentials)
    if fetched:
        assignments.append("last_fetch_at = now()")
    params.append(user_id)

    with write_connection() as conn:
        conn.execute(
            f"""
            UPDATE gmail_oauth_connections
            SET {", ".join(assignments)}
            WHERE user_id = %s
            """,
            tuple(params),
        )
        conn.commit()


def _import_credentials_modules() -> tuple[Any, Any]:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gmail API dependencies are not installed.",
        ) from exc
    return Request, Credentials


def _load_connected_credentials(user_id: str) -> Any:
    Request, Credentials = _import_credentials_modules()
    try:
        credentials = Credentials.from_authorized_user_info(json.loads(_connection_credentials(user_id)), GMAIL_SCOPES)
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            _mark_connection_status(
                user_id,
                status_value="connected",
                encrypted_credentials=encrypt_credentials(credentials.to_json()),
            )
    except HTTPException:
        raise
    except Exception as exc:
        _mark_connection_status(user_id, status_value="token_expired", last_error=str(exc))
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=SAFE_GMAIL_RECONNECT_ERROR) from exc

    if not credentials.valid:
        _mark_connection_status(user_id, status_value="token_expired", last_error="Stored Gmail credentials are invalid.")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=SAFE_GMAIL_RECONNECT_ERROR)
    return credentials


def _default_source_queries() -> dict[str, str]:
    try:
        config = load_users_config()
    except ConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_GMAIL_QUERY_ERROR) from exc
    for preferences in config.preferences.values():
        if preferences.source_queries:
            return dict(preferences.source_queries)
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_GMAIL_QUERY_ERROR)


def _source_queries(preferences: UserPreferencesResponse) -> dict[str, str]:
    return preferences.sourceQueries or _default_source_queries()


def _preference_model(preferences: UserPreferencesResponse, *, source_queries: dict[str, str]) -> UserPreferences:
    return UserPreferences(
        user_id=preferences.userId,
        target_role_keywords=tuple(preferences.targetRoleKeywords),
        preferred_locations=tuple(preferences.preferredLocations),
        excluded_keywords=tuple(preferences.excludedKeywords),
        source_queries=source_queries,
    )


def run_connected_gmail_fetch(user_id: str, *, max_results_per_source: int = 10) -> GmailFetchResponse:
    if max_results_per_source < 1:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="max_results_per_source must be at least 1.")

    preferences = get_preferences(user_id)
    source_queries = _source_queries(preferences)
    credentials = _load_connected_credentials(user_id)
    service = build_gmail_service(credentials)

    try:
        summary = run_ingestion_with_fetch(
            require_database_url(),
            user_id=user_id,
            preferences=_preference_model(preferences, source_queries=source_queries),
            fetch_contents=lambda: fetch_alert_content_with_service(
                service,
                user_id=user_id,
                source_queries=source_queries,
                max_results_per_source=max_results_per_source,
            ),
            mode="gmail_web_fetch",
        )
    except HTTPException:
        raise
    except Exception as exc:
        _mark_connection_status(user_id, status_value="fetch_failed", last_error=str(exc))
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_GMAIL_FETCH_ERROR) from exc

    _mark_connection_status(user_id, status_value="connected", fetched=True)
    warnings = list(summary.warnings)
    if summary.fetched_count == 0:
        warnings.append(SAFE_GMAIL_EMPTY_RESULT_WARNING)
    return GmailFetchResponse(
        run_id=summary.ingestion_run_id,
        scanned_message_count=summary.fetched_count,
        parsed_job_count=summary.parsed_count,
        new_job_count=summary.new_count,
        seen_before_count=summary.seen_again_count,
        skipped_count=summary.skipped_count,
        source_counts=_source_counts_for_response(source_queries, dict(summary.source_counts)),
        warnings=warnings,
    )
