from __future__ import annotations

import json

import pytest
from fastapi import HTTPException

from api.services import gemini_analysis_service as gemini_service
from api.services.gemini_analysis_service import AnalysisJobInput


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

    results = gemini_service._validate_results(raw, expected_job_ids=[4])

    assert results[0].priority == "High"
    assert results[0].score == 8.5


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


def test_build_prompt_uses_compact_job_data_and_preferences(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        gemini_service,
        "_profile_context",
        lambda user_id: {
            "target_role_keywords": ["Werkstudent AI"],
            "preferred_locations": ["Berlin"],
            "excluded_keywords": ["Senior"],
            "profile_source": "auth_scoped_preferences",
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
    assert "auth_scoped_preferences" in prompt
    assert "resume" not in prompt.casefold()
    assert "gmail" not in prompt.casefold()
