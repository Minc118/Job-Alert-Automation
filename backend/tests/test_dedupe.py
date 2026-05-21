from __future__ import annotations

from job_alert_automation.dedupe import (
    build_job_dedupe_key,
    dedupe_jobs,
    hash_normalized_url,
    normalize_text,
    normalize_url,
)
from job_alert_automation.models import ParsedJob


def test_normalize_text_lowercases_and_collapses_spaces() -> None:
    assert normalize_text("  Werkstudent\u00a0 AI   Berlin  ") == "werkstudent ai berlin"


def test_normalize_url_removes_tracking_params_and_fragment() -> None:
    normalized = normalize_url(
        "HTTPS://Example.COM/jobs/123?utm_source=x&gclid=y&id=42&utm_medium=z#details"
    )

    assert normalized == "https://example.com/jobs/123?id=42"


def test_url_hash_is_stable() -> None:
    normalized = "https://example.com/jobs/123?id=42"

    assert hash_normalized_url(normalized) == hash_normalized_url(normalized)


def test_url_based_dedupe_uses_source_and_normalized_url_hash() -> None:
    job = ParsedJob(
        source="LinkedIn",
        title="Werkstudent AI",
        company="Acme",
        location="Berlin",
        url="https://example.com/job?utm_campaign=a&id=1",
    )

    key = build_job_dedupe_key(job)

    assert key.kind == "url"
    assert key.source == "linkedin"
    assert key.parts[0] == "linkedin"
    assert key.parts[1] == hash_normalized_url("https://example.com/job?id=1")


def test_missing_url_fallback_uses_normalized_fields() -> None:
    job = ParsedJob(
        source="StepStone",
        title=" Junior  Project Manager ",
        company=" Example GmbH ",
        location=" Berlin ",
    )

    key = build_job_dedupe_key(job)

    assert key.kind == "fallback"
    assert key.parts == ("stepstone", "junior project manager", "example gmbh", "berlin")


def test_dedupe_jobs_preserves_first_occurrence() -> None:
    first = ParsedJob(source="Indeed", title="Developer", company="Acme", location="Berlin")
    duplicate = ParsedJob(source="Indeed", title=" developer ", company="ACME", location="Berlin")
    other = ParsedJob(source="Indeed", title="Developer", company="Other", location="Berlin")

    unique_jobs, summary = dedupe_jobs([first, duplicate, other])

    assert unique_jobs == [first, other]
    assert summary == {"input_count": 3, "unique_count": 2, "duplicate_count": 1}


def test_dedupe_keeps_different_sources_separate() -> None:
    linkedin = ParsedJob(source="LinkedIn", title="Developer", company="Acme", location="Berlin")
    indeed = ParsedJob(source="Indeed", title="Developer", company="Acme", location="Berlin")

    unique_jobs, summary = dedupe_jobs([linkedin, indeed])

    assert unique_jobs == [linkedin, indeed]
    assert summary["duplicate_count"] == 0
