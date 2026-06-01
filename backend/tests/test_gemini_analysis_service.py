from __future__ import annotations

import json

import pytest
from fastapi import HTTPException

from api.services import gemini_analysis_service as gemini_service
from api.services.gemini_analysis_service import AnalysisJobInput
from job_alert_automation.config import ConfigError


class _FakeWriteConnection:
    def __enter__(self) -> "_FakeWriteConnection":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def commit(self) -> None:
        return None


def _analysis_job(job_id: int = 9, short_description: str = "Short safe job summary only.") -> AnalysisJobInput:
    return AnalysisJobInput(
        job_id=job_id,
        title="Automation Associate",
        company="Example",
        location="Berlin",
        source="linkedin",
        short_description=short_description,
        matched_keywords=("Automation",),
        matched_locations=("Berlin",),
        current_status="new",
        discovery="seen_before",
    )


def _patch_successful_runtime(monkeypatch: pytest.MonkeyPatch, *, raw_json: str) -> list[dict[str, object]]:
    inserted: list[dict[str, object]] = []
    monkeypatch.setattr(gemini_service, "_analysis_limit", lambda: 20)
    monkeypatch.setattr(gemini_service, "_load_owned_jobs", lambda user_id, job_ids: [_analysis_job(job_id) for job_id in job_ids])
    monkeypatch.setattr(gemini_service, "_gemini_settings", lambda: ("test-api-key", "gemini-test-model"))
    monkeypatch.setattr(
        gemini_service,
        "_profile_context",
        lambda user_id: {
            "target_role_keywords": ["Automation"],
            "preferred_locations": ["Berlin"],
            "excluded_keywords": [],
            "profile_source": "active_profile_markdown",
            "active_profile_summary": "Compact fictional profile summary.",
        },
    )
    monkeypatch.setattr(gemini_service, "_generate_gemini_json", lambda **kwargs: raw_json)
    monkeypatch.setattr(gemini_service, "write_connection", _FakeWriteConnection)
    monkeypatch.setattr(gemini_service, "create_runtime_analysis_batch", lambda conn, **kwargs: 88)
    monkeypatch.setattr(gemini_service, "mark_analysis_batch_completed", lambda conn, **kwargs: None)
    monkeypatch.setattr(gemini_service, "mark_analysis_batch_failed", lambda conn, **kwargs: None)
    monkeypatch.setattr(gemini_service, "insert_analysis", lambda conn, **kwargs: inserted.append(kwargs))
    return inserted


def test_validate_results_requires_expected_jobs() -> None:
    raw = json.dumps(
        {
            "results": [
                {
                    "job_id": 4,
                    "score": 8.5,
                    "priority": "High",
                    "reason": "Strong role fit.",
                    "concern": "Check availability.",
                    "suggested_status": "saved",
                }
            ]
        }
    )

    validation = gemini_service._validate_results(raw, expected_job_ids=[4])

    assert validation.results[0].priority == "High"
    assert validation.results[0].score == 8.5
    assert validation.failed_count == 0


def test_validate_results_rejects_invalid_priority() -> None:
    raw = json.dumps(
        {
            "results": [
                {
                    "job_id": 4,
                    "score": 8.5,
                    "priority": "Urgent",
                    "reason": "Strong role fit.",
                    "concern": "Check availability.",
                    "suggested_status": "saved",
                }
            ]
        }
    )

    with pytest.raises(HTTPException) as exc_info:
        gemini_service._validate_results(raw, expected_job_ids=[4])

    assert exc_info.value.status_code == 502


def test_validate_results_skips_invalid_per_job_output() -> None:
    raw = json.dumps(
        {
            "results": [
                {
                    "job_id": 4,
                    "score": 8.5,
                    "priority": "High",
                    "reason": "Strong role fit.",
                    "concern": "Check availability.",
                    "suggested_status": "saved",
                },
                {
                    "job_id": 5,
                    "score": 11,
                    "priority": "High",
                    "reason": "Invalid score.",
                    "concern": "Invalid score.",
                    "suggested_status": "saved",
                },
            ]
        }
    )

    validation = gemini_service._validate_results(raw, expected_job_ids=[4, 5])

    assert [result.job_id for result in validation.results] == [4]
    assert validation.failed_count == 1
    assert validation.warnings


def test_build_prompt_uses_compact_job_data_and_preferences(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        gemini_service,
        "_profile_context",
        lambda user_id: {
            "target_role_keywords": ["Werkstudent AI"],
            "preferred_locations": ["Berlin"],
            "excluded_keywords": ["Senior"],
            "profile_source": "active_profile_markdown",
            "active_profile_summary": "Fictional profile summary for software automation roles.",
        },
    )
    prompt = gemini_service.build_gemini_prompt(
        "auth_profile_123",
        [
            AnalysisJobInput(
                job_id=9,
                title="Werkstudent Automation",
                company="Example",
                location="Berlin",
                source="linkedin",
                short_description="Build internal automation.",
                matched_keywords=("Werkstudent AI",),
                matched_locations=("Berlin",),
                current_status="new",
                discovery="new_in_this_run",
            )
        ],
    )

    assert "Werkstudent Automation" in prompt
    assert "active_profile_markdown" in prompt
    assert "resume" not in prompt.casefold()
    assert "gmail" not in prompt.casefold()


def test_profile_context_requires_active_profile_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        gemini_service,
        "get_preferences",
        lambda user_id: type(
            "Preferences",
            (),
            {
                "targetRoleKeywords": ["AI"],
                "preferredLocations": ["Berlin"],
                "excludedKeywords": [],
            },
        )(),
    )
    monkeypatch.setattr(gemini_service, "load_active_profile_summary", lambda user_id: None)

    with pytest.raises(HTTPException) as exc_info:
        gemini_service._profile_context("auth_profile_123")

    assert exc_info.value.status_code == 409


def test_build_prompt_excludes_raw_gmail_body_and_resume_pdf(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        gemini_service,
        "_profile_context",
        lambda user_id: {
            "target_role_keywords": ["Automation"],
            "preferred_locations": ["Berlin"],
            "excluded_keywords": [],
            "profile_source": "active_profile_markdown",
            "active_profile_summary": "Compact fictional summary.",
        },
    )
    prompt = gemini_service.build_gemini_prompt(
        "auth_profile_123",
        [
            AnalysisJobInput(
                job_id=9,
                title="Automation Associate",
                company="Example",
                location="Berlin",
                source="linkedin",
                short_description="Short safe job summary only.",
                matched_keywords=("Automation",),
                matched_locations=("Berlin",),
                current_status="new",
                discovery="seen_before",
            )
        ],
    )

    assert "Short safe job summary only." in prompt
    assert "raw gmail body sentinel" not in prompt.casefold()
    assert "pdf" not in prompt.casefold()


def test_gemini_settings_missing_api_key_fails_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_get_env_value(name: str, *, default: str | None = None, env_path=None) -> str:
        if name == "GEMINI_API_KEY":
            raise ConfigError("missing")
        return default or "gemini"

    monkeypatch.setattr(gemini_service, "get_env_value", fake_get_env_value)

    with pytest.raises(HTTPException) as exc_info:
        gemini_service._gemini_settings()

    assert exc_info.value.status_code == 503
    assert "AI analysis is not configured" in str(exc_info.value.detail)


def test_run_gemini_analysis_stores_valid_json_and_returns_safe_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    inserted = _patch_successful_runtime(
        monkeypatch,
        raw_json=json.dumps(
            {
                "results": [
                    {
                        "job_id": 9,
                        "score": 8.4,
                        "priority": "High",
                        "reason": "Strong automation fit.",
                        "concern": "Confirm weekly availability.",
                        "suggested_status": "saved",
                    }
                ]
            }
        ),
    )

    response = gemini_service.run_gemini_analysis("auth_profile_123", gemini_service.AnalysisRunCreate(jobIds=[9]))

    assert response.analysis_batch_id == 88
    assert response.provider == "gemini"
    assert response.model == "gemini-test-model"
    assert response.requested_job_count == 1
    assert response.analyzed_count == 1
    assert response.failed_count == 0
    assert response.results[0].job_id == 9
    assert inserted[0]["provider"] == "gemini"
    assert inserted[0]["source_file"] == "gemini:gemini-test-model"
    safe_payload = response.model_dump()
    assert "profile" not in str(safe_payload).casefold()
    assert "prompt" not in str(safe_payload).casefold()
    assert "body" not in str(safe_payload).casefold()


def test_run_gemini_analysis_invalid_json_fails_without_insert(monkeypatch: pytest.MonkeyPatch) -> None:
    inserted = _patch_successful_runtime(monkeypatch, raw_json="{not valid json")

    with pytest.raises(HTTPException) as exc_info:
        gemini_service.run_gemini_analysis("auth_profile_123", gemini_service.AnalysisRunCreate(jobIds=[9]))

    assert exc_info.value.status_code == 502
    assert inserted == []
