from __future__ import annotations

from dataclasses import dataclass

from .config import load_users_config
from .dedupe import dedupe_jobs
from .email_parser import parse_email_contents
from .filters import evaluate_jobs_relevance
from .gmail_client import fetch_recent_alert_content
from .models import JobFilterResult


@dataclass(frozen=True)
class DryRunPreview:
    user_id: str
    fetched_email_count: int
    parsed_job_count: int
    unique_job_count: int
    duplicate_job_count: int
    likely_relevant_count: int
    unlikely_relevant_count: int
    results: tuple[JobFilterResult, ...]


def build_dry_run_preview(user_id: str, *, max_results_per_source: int = 10) -> DryRunPreview:
    config = load_users_config()
    config.validate_user_id(user_id)
    preferences = config.preferences[user_id]

    email_contents = fetch_recent_alert_content(user_id, max_results_per_source=max_results_per_source)
    parsed_jobs = parse_email_contents(email_contents)
    unique_jobs, dedupe_summary = dedupe_jobs(parsed_jobs)
    results = evaluate_jobs_relevance(unique_jobs, preferences)
    likely_count = sum(1 for result in results if result.likely_relevant)

    return DryRunPreview(
        user_id=user_id,
        fetched_email_count=len(email_contents),
        parsed_job_count=len(parsed_jobs),
        unique_job_count=len(unique_jobs),
        duplicate_job_count=dedupe_summary["duplicate_count"],
        likely_relevant_count=likely_count,
        unlikely_relevant_count=len(results) - likely_count,
        results=tuple(results),
    )


def format_dry_run_preview(preview: DryRunPreview, *, max_jobs: int = 10) -> str:
    lines = [
        f"Dry-run preview for user '{preview.user_id}':",
        f"  emails fetched: {preview.fetched_email_count}",
        f"  jobs parsed: {preview.parsed_job_count}",
        f"  unique jobs: {preview.unique_job_count}",
        f"  duplicates removed: {preview.duplicate_job_count}",
        f"  likely relevant: {preview.likely_relevant_count}",
        f"  unlikely relevant: {preview.unlikely_relevant_count}",
    ]

    if not preview.results:
        lines.append("  candidates: none")
        return "\n".join(lines)

    lines.append("  candidate preview:")
    sorted_results = sorted(preview.results, key=lambda result: result.likely_relevant, reverse=True)
    for index, result in enumerate(sorted_results[:max_jobs], start=1):
        job = result.job
        relevance = "likely" if result.likely_relevant else "unlikely"
        company = job.company or "Unknown company"
        location = job.location or "Unknown location"
        lines.append(f"    {index}. [{relevance}] {job.title} - {company} - {location} ({job.source})")
        if result.relevance_reason:
            lines.append(f"       reason: {result.relevance_reason}")

    remaining = len(preview.results) - max_jobs
    if remaining > 0:
        lines.append(f"    ... {remaining} more candidate(s) not shown")
    lines.append("  no database writes were performed")
    return "\n".join(lines)
