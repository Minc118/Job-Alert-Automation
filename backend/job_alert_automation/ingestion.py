from __future__ import annotations

from collections.abc import Callable
from collections import Counter

from .database import connect
from .dedupe import dedupe_jobs
from .email_parser import parse_email_content
from .filters import evaluate_jobs_relevance
from .gmail_client import fetch_recent_alert_content
from .models import EmailMessageContent, UserPreferences
from .repository import (
    IngestionPersistSummary,
    complete_ingestion_run,
    create_ingestion_run,
    fail_ingestion_run,
    upsert_email_message,
    upsert_job,
    upsert_user_job,
)


def run_ingestion_for_user(database_url: str, *, user_id: str, max_results_per_source: int = 10) -> IngestionPersistSummary:
    from .config import load_users_config

    preferences = load_users_config().preferences[user_id]
    return run_ingestion_with_fetch(
        database_url,
        user_id=user_id,
        preferences=preferences,
        fetch_contents=lambda: fetch_recent_alert_content(user_id, max_results_per_source=max_results_per_source),
        mode="run_now",
    )


def run_ingestion_with_fetch(
    database_url: str,
    *,
    user_id: str,
    preferences: UserPreferences,
    fetch_contents: Callable[[], list[EmailMessageContent]],
    mode: str,
) -> IngestionPersistSummary:
    with connect(database_url) as conn:
        ingestion_run_id = create_ingestion_run(conn, selected_user_id=user_id, mode=mode)
        try:
            contents = fetch_contents()
            parsed_jobs = []
            parser_skipped_count = 0
            warnings: list[str] = []
            source_counts = Counter(
                str(content.metadata.source or "unknown")
                for content in contents
            )
            for content in contents:
                try:
                    parsed_jobs.extend(parse_email_content(content))
                except Exception:
                    parser_skipped_count += 1
            if parser_skipped_count:
                warnings.append(f"Skipped {parser_skipped_count} message(s) because parsing failed.")

            unique_jobs, _dedupe_summary = dedupe_jobs(parsed_jobs)
            duplicate_count = len(parsed_jobs) - len(unique_jobs)
            if duplicate_count:
                warnings.append(f"Skipped {duplicate_count} duplicate job(s).")
            results = evaluate_jobs_relevance(unique_jobs, preferences)

            new_count = 0
            likely_count = 0
            for content in contents:
                upsert_email_message(conn, content=content)

            for result in results:
                job_id = upsert_job(conn, job=result.job)
                seen_as_new = upsert_user_job(
                    conn,
                    user_id=user_id,
                    job_id=job_id,
                    ingestion_run_id=ingestion_run_id,
                    result=result,
                )
                if seen_as_new:
                    new_count += 1
                if result.likely_relevant:
                    likely_count += 1

            summary = IngestionPersistSummary(
                ingestion_run_id=ingestion_run_id,
                fetched_count=len(contents),
                parsed_count=len(parsed_jobs),
                unique_count=len(unique_jobs),
                new_count=new_count,
                seen_again_count=len(results) - new_count,
                likely_relevant_count=likely_count,
                skipped_count=parser_skipped_count + duplicate_count,
                source_counts=dict(source_counts),
                warnings=tuple(warnings),
            )
            complete_ingestion_run(conn, ingestion_run_id=ingestion_run_id, summary=summary)
            conn.commit()
            return summary
        except Exception as exc:
            fail_ingestion_run(conn, ingestion_run_id=ingestion_run_id, error_message=str(exc))
            conn.commit()
            raise
