from __future__ import annotations

from collections.abc import Iterable

from .email_content import preferred_text_body
from .models import EmailMessageContent, ParsedJob
from .sources import parse_indeed_alert, parse_linkedin_alert, parse_stepstone_alert


SOURCE_PARSERS = {
    "linkedin": parse_linkedin_alert,
    "stepstone": parse_stepstone_alert,
    "indeed": parse_indeed_alert,
}


def parse_job_alert_body(source: str | None, body: str | None) -> list[ParsedJob]:
    if not source:
        return []
    parser = SOURCE_PARSERS.get(source.lower())
    if parser is None:
        return []
    return parser(body)


def parse_email_content(content: EmailMessageContent) -> list[ParsedJob]:
    body = preferred_text_body(content.text_body, content.html_body)
    jobs = parse_job_alert_body(content.metadata.source, body)
    enriched: list[ParsedJob] = []
    for job in jobs:
        metadata = {
            **job.metadata,
            "gmail_message_id": content.metadata.gmail_message_id,
            "gmail_thread_id": content.metadata.gmail_thread_id,
            "body_hash": content.body_hash or content.metadata.body_hash,
        }
        enriched.append(
            ParsedJob(
                source=job.source,
                title=job.title,
                company=job.company,
                location=job.location,
                url=job.url,
                short_description=job.short_description,
                metadata=metadata,
            )
        )
    return enriched


def parse_email_contents(contents: Iterable[EmailMessageContent]) -> list[ParsedJob]:
    jobs: list[ParsedJob] = []
    for content in contents:
        jobs.extend(parse_email_content(content))
    return jobs
