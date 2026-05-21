from __future__ import annotations

from .database import connect
from .dedupe import dedupe_jobs
from .email_parser import parse_email_contents
from .filters import evaluate_jobs_relevance
from .gmail_client import fetch_recent_alert_content
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
    with connect(database_url) as conn:
        ingestion_run_id = create_ingestion_run(conn, selected_user_id=user_id, mode="run_now")
        try:
            contents = fetch_recent_alert_content(user_id, max_results_per_source=max_results_per_source)
            parsed_jobs = parse_email_contents(contents)
            unique_jobs, _dedupe_summary = dedupe_jobs(parsed_jobs)

            from .config import load_users_config

            preferences = load_users_config().preferences[user_id]
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
            )
            complete_ingestion_run(conn, ingestion_run_id=ingestion_run_id, summary=summary)
            conn.commit()
            return summary
        except Exception as exc:
            fail_ingestion_run(conn, ingestion_run_id=ingestion_run_id, error_message=str(exc))
            conn.commit()
            raise
