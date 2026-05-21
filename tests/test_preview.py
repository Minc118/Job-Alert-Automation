from __future__ import annotations

from job_alert_automation.models import EmailMessageContent, EmailMessageMetadata, JobFilterResult, ParsedJob
from job_alert_automation.preview import DryRunPreview, build_dry_run_preview, format_dry_run_preview


def test_build_dry_run_preview_fetches_parses_dedupes_and_filters(monkeypatch) -> None:
    contents = [
        EmailMessageContent(
            metadata=EmailMessageMetadata(user_id="minjian", gmail_message_id="msg-1", source="linkedin"),
            text_body="""
            Title: Werkstudent AI Automation
            Company: Example Labs
            Location: Berlin
            URL: https://example.com/job?id=1&utm_source=email
            Description: Build automation tools.
            """,
        ),
        EmailMessageContent(
            metadata=EmailMessageMetadata(user_id="minjian", gmail_message_id="msg-2", source="linkedin"),
            text_body="""
            Title: Werkstudent AI Automation
            Company: Example Labs
            Location: Berlin
            URL: https://example.com/job?id=1&utm_medium=email
            Description: Build automation tools.
            """,
        ),
    ]

    monkeypatch.setattr(
        "job_alert_automation.preview.fetch_recent_alert_content",
        lambda user_id, *, max_results_per_source: contents,
    )

    preview = build_dry_run_preview("minjian", max_results_per_source=5)

    assert preview.user_id == "minjian"
    assert preview.fetched_email_count == 2
    assert preview.parsed_job_count == 2
    assert preview.unique_job_count == 1
    assert preview.duplicate_job_count == 1
    assert preview.likely_relevant_count == 1


def test_format_dry_run_preview_is_compact_and_does_not_include_body() -> None:
    unlikely_job = ParsedJob(
        source="linkedin",
        title="Warehouse Helper",
        company="Example Logistics",
        location="Berlin",
    )
    likely_job = ParsedJob(
        source="linkedin",
        title="Werkstudent AI",
        company="Example Labs",
        location="Berlin",
        short_description="Sensitive body text should not be printed.",
    )
    preview = DryRunPreview(
        user_id="minjian",
        fetched_email_count=1,
        parsed_job_count=1,
        unique_job_count=1,
        duplicate_job_count=0,
        likely_relevant_count=1,
        unlikely_relevant_count=1,
        results=(
            JobFilterResult(
                job=unlikely_job,
                likely_relevant=False,
                relevance_reason="no configured role or location keywords matched",
            ),
            JobFilterResult(
                job=likely_job,
                likely_relevant=True,
                matched_keywords=("werkstudent ai",),
                matched_locations=("berlin",),
                relevance_reason="matched role keyword(s): werkstudent ai",
            ),
        ),
    )

    output = format_dry_run_preview(preview)

    assert "Dry-run preview for user 'minjian'" in output
    assert "Werkstudent AI - Example Labs - Berlin" in output
    assert "Sensitive body text" not in output
    assert output.index("[likely] Werkstudent AI") < output.index("[unlikely] Warehouse Helper")
