from __future__ import annotations

from job_alert_automation.config import load_users_config
from job_alert_automation.filters import evaluate_job_relevance, evaluate_jobs_relevance
from job_alert_automation.models import ParsedJob, UserPreferences


def test_evaluate_job_relevance_matches_minjian_keywords_and_location() -> None:
    preferences = load_users_config().preferences["minjian"]
    job = ParsedJob(
        source="linkedin",
        title="Werkstudent AI Automation",
        company="Example Labs",
        location="Hybrid Berlin",
        short_description="Build automation tools for data workflows.",
    )

    result = evaluate_job_relevance(job, preferences)

    assert result.likely_relevant is True
    assert "werkstudent ai" in result.matched_keywords
    assert "berlin" in result.matched_locations
    assert not result.exclusion_matches
    assert result.relevance_reason


def test_evaluate_job_relevance_matches_multiword_terms_order_insensitively() -> None:
    preferences = load_users_config().preferences["minjian"]
    job = ParsedJob(
        source="linkedin",
        title="Data Analysis Werkstudent:in",
        company="Enpal",
        location="Berlin",
    )

    result = evaluate_job_relevance(job, preferences)

    assert result.likely_relevant is True
    assert "werkstudent data" in result.matched_keywords


def test_evaluate_job_relevance_excludes_obvious_irrelevant_jobs() -> None:
    preferences = load_users_config().preferences["minjian"]
    job = ParsedJob(
        source="stepstone",
        title="Senior Werkstudent AI Lead",
        company="Example Labs",
        location="Berlin",
    )

    result = evaluate_job_relevance(job, preferences)

    assert result.likely_relevant is False
    assert "senior" in result.exclusion_matches
    assert "lead" in result.exclusion_matches


def test_evaluate_job_relevance_handles_no_keyword_match() -> None:
    preferences = load_users_config().preferences["chang"]
    job = ParsedJob(
        source="indeed",
        title="Warehouse Helper",
        company="Example Logistics",
        location="Berlin",
    )

    result = evaluate_job_relevance(job, preferences)

    assert result.likely_relevant is False
    assert result.matched_locations
    assert not result.matched_keywords


def test_evaluate_jobs_relevance_returns_results_for_all_jobs() -> None:
    preferences = UserPreferences(
        user_id="test",
        target_role_keywords=("project management",),
        preferred_locations=("remote",),
        excluded_keywords=("director",),
    )
    jobs = [
        ParsedJob(source="indeed", title="Project Management Coordinator", location="Remote"),
        ParsedJob(source="indeed", title="Director Project Management", location="Remote"),
    ]

    results = evaluate_jobs_relevance(jobs, preferences)

    assert [result.likely_relevant for result in results] == [True, False]
