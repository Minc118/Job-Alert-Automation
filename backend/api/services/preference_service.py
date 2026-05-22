from __future__ import annotations

from typing import Any

from api.schemas import UserPreferencesResponse, UserPreferencesUpdate
from api.services.database import readonly_connection, write_connection


def _clean_terms(values: list[str]) -> list[str]:
    seen: set[str] = set()
    terms: list[str] = []
    for value in values:
        cleaned = value.strip()
        normalized = cleaned.casefold()
        if cleaned and normalized not in seen:
            seen.add(normalized)
            terms.append(cleaned)
    return terms


def _row_to_preferences(row: Any) -> UserPreferencesResponse:
    return UserPreferencesResponse(
        userId=str(row[0]),
        targetRoleKeywords=list(row[1] or []),
        preferredLocations=list(row[2] or []),
        excludedKeywords=list(row[3] or []),
        sourceQueries=dict(row[4] or {}),
    )


def get_preferences(user_id: str) -> UserPreferencesResponse:
    with readonly_connection() as conn:
        row = conn.execute(
            """
            SELECT user_id, target_role_keywords, preferred_locations, excluded_keywords, source_queries
            FROM user_preferences
            WHERE user_id = %s
            """,
            (user_id,),
        ).fetchone()
    if row is None:
        return UserPreferencesResponse(
            userId=user_id,
            targetRoleKeywords=[],
            preferredLocations=[],
            excludedKeywords=[],
            sourceQueries={},
        )
    return _row_to_preferences(row)


def update_preferences(user_id: str, payload: UserPreferencesUpdate) -> UserPreferencesResponse:
    target_roles = _clean_terms(payload.targetRoleKeywords)
    locations = _clean_terms(payload.preferredLocations)
    exclusions = _clean_terms(payload.excludedKeywords)
    with write_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO user_preferences (
                user_id,
                target_role_keywords,
                preferred_locations,
                excluded_keywords
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET target_role_keywords = EXCLUDED.target_role_keywords,
                preferred_locations = EXCLUDED.preferred_locations,
                excluded_keywords = EXCLUDED.excluded_keywords,
                updated_at = now()
            RETURNING user_id, target_role_keywords, preferred_locations, excluded_keywords, source_queries
            """,
            (user_id, target_roles, locations, exclusions),
        ).fetchone()
        conn.commit()
    return _row_to_preferences(row)
