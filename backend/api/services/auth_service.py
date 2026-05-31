from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
from typing import Any

import jwt
from fastapi import HTTPException, status
from jwt import InvalidTokenError, PyJWKClient
from jwt.exceptions import PyJWKClientError

from api.schemas import AppUserProfileResponse
from api.services.database import readonly_connection, write_connection
from job_alert_automation.config import ConfigError, get_env_value


SAFE_AUTH_CONFIG_ERROR = "Neon Auth verification is not configured. Add NEON_AUTH_JWKS_URL to the local .env file."
SAFE_AUTH_UNAVAILABLE_ERROR = "Neon Auth verification is unavailable. Check local configuration and network access."
SAFE_AUTH_TOKEN_ERROR = "Authentication token is invalid or expired."
ALLOWED_JWT_ALGORITHMS = {"EdDSA", "ES256", "ES384", "ES512", "RS256", "RS384", "RS512"}


@dataclass(frozen=True)
class VerifiedIdentity:
    subject: str
    display_name: str | None
    email: str | None


@dataclass(frozen=True)
class AuthenticatedAppProfile:
    user: AppUserProfileResponse
    onboarding_complete: bool


def _optional_claim(payload: dict[str, Any], *names: str) -> str | None:
    for name in names:
        value = payload.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def require_neon_auth_jwks_url() -> str:
    try:
        return get_env_value("NEON_AUTH_JWKS_URL")
    except ConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_AUTH_CONFIG_ERROR) from exc


@lru_cache(maxsize=4)
def _jwks_client(jwks_url: str) -> PyJWKClient:
    # PyJWKClient caches fetched keys; keep it across requests so protected API
    # calls do not refetch Neon JWKS for every dashboard request.
    return PyJWKClient(jwks_url)


def verify_neon_auth_jwt(token: str) -> VerifiedIdentity:
    jwks_url = require_neon_auth_jwks_url()
    try:
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg")
        if algorithm not in ALLOWED_JWT_ALGORITHMS:
            raise InvalidTokenError("Unsupported JWT algorithm.")

        signing_key = _jwks_client(jwks_url).get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=[algorithm],
            # Neon Auth JWTs can carry an audience for Data API/RLS use. This API
            # trusts the configured Neon JWKS and does not have a separate audience
            # value to validate yet.
            options={"verify_aud": False},
        )
    except PyJWKClientError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_AUTH_UNAVAILABLE_ERROR) from exc
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=SAFE_AUTH_TOKEN_ERROR) from exc

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=SAFE_AUTH_TOKEN_ERROR)

    return VerifiedIdentity(
        subject=subject.strip(),
        display_name=_optional_claim(payload, "name", "display_name"),
        email=_optional_claim(payload, "email"),
    )


def _new_app_user_id(auth_subject: str) -> str:
    digest = hashlib.sha256(auth_subject.encode("utf-8")).hexdigest()[:24]
    return f"auth_{digest}"


def _profile_from_row(row: Any) -> AuthenticatedAppProfile:
    return AuthenticatedAppProfile(
        user=AppUserProfileResponse(id=str(row[0]), displayName=str(row[1])),
        onboarding_complete=bool(row[2]),
    )


def get_app_profile(identity: VerifiedIdentity) -> AuthenticatedAppProfile | None:
    with readonly_connection() as conn:
        row = conn.execute(
            """
            SELECT p.user_id, u.display_name, p.onboarding_complete
            FROM app_user_profiles p
            JOIN app_users u ON u.id = p.user_id
            WHERE p.auth_subject = %s AND p.auth_provider = 'neon'
            """,
            (identity.subject,),
        ).fetchone()
    return _profile_from_row(row) if row else None


def get_or_create_app_profile(identity: VerifiedIdentity) -> AuthenticatedAppProfile:
    existing = get_app_profile(identity)
    if existing:
        return existing

    user_id = _new_app_user_id(identity.subject)
    display_name = identity.display_name or identity.email or "Signed In User"
    with write_connection() as conn:
        conn.execute(
            """
            INSERT INTO app_users (id, display_name, email)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE
            SET display_name = EXCLUDED.display_name,
                email = EXCLUDED.email,
                updated_at = now()
            """,
            (user_id, display_name, identity.email),
        )
        conn.execute(
            """
            INSERT INTO user_preferences (user_id)
            VALUES (%s)
            ON CONFLICT (user_id) DO NOTHING
            """,
            (user_id,),
        )
        conn.execute(
            """
            INSERT INTO app_user_profiles (
                auth_subject,
                user_id,
                auth_provider,
                display_name,
                email
            )
            VALUES (%s, %s, 'neon', %s, %s)
            ON CONFLICT (auth_subject) DO UPDATE
            SET display_name = EXCLUDED.display_name,
                email = EXCLUDED.email,
                updated_at = now()
            """,
            (identity.subject, user_id, identity.display_name, identity.email),
        )
        conn.commit()

    created = get_app_profile(identity)
    if created is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authenticated app profile could not be loaded.")
    return created


def complete_onboarding(identity: VerifiedIdentity) -> AuthenticatedAppProfile:
    profile = get_or_create_app_profile(identity)
    with write_connection() as conn:
        conn.execute(
            """
            UPDATE app_user_profiles
            SET onboarding_complete = true,
                updated_at = now()
            WHERE auth_subject = %s AND auth_provider = 'neon'
            """,
            (identity.subject,),
        )
        conn.commit()

    completed = get_app_profile(identity)
    if completed is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authenticated app profile could not be loaded.")
    return completed
