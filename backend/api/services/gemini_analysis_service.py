from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError, field_validator

from api.schemas import AnalysisRunCreate, AnalysisRunResponse
from api.services.database import readonly_connection, write_connection
from api.services.document_service import load_active_profile_summary
from api.services.preference_service import get_preferences
from job_alert_automation.config import ConfigError, get_env_value
from job_alert_automation.repository import (
    create_runtime_analysis_batch,
    insert_analysis,
    mark_analysis_batch_completed,
    mark_analysis_batch_failed,
)


SAFE_GEMINI_CONFIG_ERROR = "Gemini analysis is not configured. Add backend Gemini settings to the local .env file."
SAFE_GEMINI_UNAVAILABLE_ERROR = "Gemini analysis failed. Check backend configuration and try again later."
SAFE_GEMINI_RESULT_ERROR = "Gemini returned an analysis result that could not be validated."
VALID_SUGGESTED_STATUSES = {"new", "saved", "applied", "ignored"}


@dataclass(frozen=True)
class AnalysisJobInput:
    job_id: int
    title: str
    company: str
    location: str
    source: str
    short_description: str
    matched_keywords: tuple[str, ...]
    matched_locations: tuple[str, ...]
    current_status: str
    discovery: str


class GeminiJobResult(BaseModel):
    job_id: int
    score: float | None = None
    priority: Literal["High", "Medium", "Low"]
    reason: str
    concern: str
    suggested_status: Literal["new", "saved", "applied", "ignored"] | None = None

    @field_validator("score")
    @classmethod
    def validate_score(cls, value: float | None) -> float | None:
        if value is not None and not 1 <= value <= 10:
            raise ValueError("score must be between 1 and 10")
        return value


class GeminiResultEnvelope(BaseModel):
    results: list[GeminiJobResult]


def _analysis_limit() -> int:
    try:
        raw = get_env_value("AI_ANALYSIS_MAX_JOBS", default="20")
        limit = int(raw)
    except (ConfigError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_GEMINI_CONFIG_ERROR) from exc
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_GEMINI_CONFIG_ERROR)
    return limit


def _gemini_settings() -> tuple[str, str]:
    try:
        provider = get_env_value("AI_PROVIDER", default="gemini").casefold()
        api_key = get_env_value("GEMINI_API_KEY")
        model = get_env_value("GEMINI_MODEL", default="gemini-2.5-flash")
    except ConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_GEMINI_CONFIG_ERROR) from exc
    if provider != "gemini" or not api_key or not model:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_GEMINI_CONFIG_ERROR)
    return api_key, model


def _unique_job_ids(payload: AnalysisRunCreate) -> list[int]:
    if not payload.jobIds:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Select at least one job for analysis.")
    unique_ids = list(dict.fromkeys(payload.jobIds))
    if any(job_id < 1 for job_id in unique_ids):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="jobIds must be positive integers.")
    limit = _analysis_limit()
    if len(unique_ids) > limit:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Select at most {limit} jobs for one Gemini analysis run.",
        )
    return unique_ids


def _discovery_label(seen_as_new: bool | None, last_seen_run_id: int | None) -> str:
    if last_seen_run_id is None:
        return "historical"
    return "new_in_this_run" if seen_as_new else "seen_before"


def _compact_text(value: str | None, *, limit: int = 1200) -> str:
    cleaned = " ".join((value or "").split())
    return cleaned[:limit]


def _load_owned_jobs(user_id: str, job_ids: list[int]) -> list[AnalysisJobInput]:
    with readonly_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                j.id,
                j.title,
                j.company,
                j.location,
                j.source,
                j.short_description,
                uj.matched_keywords,
                uj.matched_locations,
                uj.status,
                jro.seen_as_new,
                uj.last_seen_run_id
            FROM user_jobs uj
            JOIN jobs j ON j.id = uj.job_id
            LEFT JOIN job_run_occurrences jro
                ON jro.user_id = uj.user_id
               AND jro.job_id = uj.job_id
               AND jro.ingestion_run_id = uj.last_seen_run_id
            WHERE uj.user_id = %s
              AND j.id = ANY(%s)
            ORDER BY j.id
            """,
            (user_id, job_ids),
        ).fetchall()

    if len(rows) != len(job_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selected jobs were not found for this account.")

    return [
        AnalysisJobInput(
            job_id=int(row[0]),
            title=str(row[1]),
            company=row[2] or "",
            location=row[3] or "",
            source=str(row[4]),
            short_description=_compact_text(row[5]),
            matched_keywords=tuple(row[6] or ()),
            matched_locations=tuple(row[7] or ()),
            current_status=str(row[8]),
            discovery=_discovery_label(row[9], row[10]),
        )
        for row in rows
    ]


def _profile_context(user_id: str) -> dict[str, Any]:
    preferences = get_preferences(user_id)
    active_profile_summary = load_active_profile_summary(user_id)
    profile_context = {
        "target_role_keywords": preferences.targetRoleKeywords,
        "preferred_locations": preferences.preferredLocations,
        "excluded_keywords": preferences.excludedKeywords,
    }
    if active_profile_summary:
        profile_context["profile_source"] = "active_profile_markdown"
        profile_context["active_profile_summary"] = active_profile_summary
        return profile_context
    profile_context["profile_source"] = "auth_scoped_preferences"
    return profile_context


def build_gemini_prompt(user_id: str, jobs: list[AnalysisJobInput]) -> str:
    compact_jobs = [
        {
            "job_id": job.job_id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "source": job.source,
            "short_description": job.short_description,
            "matched_keywords": list(job.matched_keywords),
            "matched_locations": list(job.matched_locations),
            "current_status": job.current_status,
            "discovery": job.discovery,
        }
        for job in jobs
    ]
    payload = {
        "user_id": user_id,
        "profile": _profile_context(user_id),
        "jobs": compact_jobs,
    }
    return "\n".join(
        [
            "Analyze these job opportunities for the authenticated user.",
            "Use only the compact profile preferences and job fields supplied below.",
            "Do not invent missing requirements.",
            "Be conservative and realistic.",
            "Return one result for every supplied job_id.",
            "Scoring: 9-10 very strong fit; 7-8 good fit; 5-6 possible fit; 1-4 weak fit or unsuitable.",
            "Suggested status is a recommendation only and must be one of new, saved, applied, ignored.",
            json.dumps(payload, ensure_ascii=False),
        ]
    )


def _response_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "job_id": {"type": "integer"},
                        "score": {"type": ["number", "null"], "minimum": 1, "maximum": 10},
                        "priority": {"type": "string", "enum": ["High", "Medium", "Low"]},
                        "reason": {"type": "string"},
                        "concern": {"type": "string"},
                        "suggested_status": {
                            "type": ["string", "null"],
                            "enum": ["new", "saved", "applied", "ignored", None],
                        },
                    },
                    "required": ["job_id", "score", "priority", "reason", "concern", "suggested_status"],
                },
            }
        },
        "required": ["results"],
    }


def _generate_gemini_json(*, api_key: str, model: str, prompt: str) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_GEMINI_CONFIG_ERROR) from exc

    try:
        response = genai.Client(api_key=api_key).models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=_response_schema(),
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_GEMINI_UNAVAILABLE_ERROR) from exc

    if not isinstance(response.text, str) or not response.text.strip():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SAFE_GEMINI_RESULT_ERROR)
    return response.text


def _validate_results(raw_json: str, *, expected_job_ids: list[int]) -> list[GeminiJobResult]:
    try:
        envelope = GeminiResultEnvelope.model_validate_json(raw_json)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=SAFE_GEMINI_RESULT_ERROR) from exc

    expected = set(expected_job_ids)
    received = [result.job_id for result in envelope.results]
    if len(received) != len(set(received)) or set(received) != expected:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=SAFE_GEMINI_RESULT_ERROR)
    return envelope.results


def run_gemini_analysis(user_id: str, payload: AnalysisRunCreate) -> AnalysisRunResponse:
    job_ids = _unique_job_ids(payload)
    jobs = _load_owned_jobs(user_id, job_ids)
    api_key, model = _gemini_settings()

    with write_connection() as conn:
        batch_id = create_runtime_analysis_batch(conn, user_id=user_id, job_count=len(job_ids))
        conn.commit()

    try:
        raw_json = _generate_gemini_json(
            api_key=api_key,
            model=model,
            prompt=build_gemini_prompt(user_id, jobs),
        )
        results = _validate_results(raw_json, expected_job_ids=job_ids)
        with write_connection() as conn:
            for result in results:
                insert_analysis(
                    conn,
                    user_id=user_id,
                    job_id=result.job_id,
                    priority=result.priority,
                    score=result.score,
                    reason=result.reason,
                    concern=result.concern,
                    suggested_status=result.suggested_status,
                    analysis_batch_id=batch_id,
                    source_file=f"gemini:{model}",
                    provider="gemini",
                )
            mark_analysis_batch_completed(conn, analysis_batch_id=batch_id)
            conn.commit()
    except HTTPException as exc:
        with write_connection() as conn:
            mark_analysis_batch_failed(conn, analysis_batch_id=batch_id, error_message=str(exc.detail))
            conn.commit()
        raise

    return AnalysisRunResponse(
        analysisBatchId=batch_id,
        userId=user_id,
        provider="gemini",
        model=model,
        requestedCount=len(payload.jobIds),
        analyzedCount=len(results),
        skippedCount=len(payload.jobIds) - len(job_ids),
        message="Gemini analysis completed. The dashboard can read the latest stored analysis.",
    )
