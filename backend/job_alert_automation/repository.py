from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from types import MappingProxyType
from typing import Any

from .database import DatabaseError
from .dedupe import hash_normalized_url, normalize_text, normalize_url
from .models import EmailMessageContent, JobFilterResult, ParsedJob


VALID_STATUSES = {"new", "saved", "applied", "ignored"}


@dataclass(frozen=True)
class StoredJob:
    job_id: int
    user_id: str
    title: str
    company: str | None
    location: str | None
    source: str
    url: str | None
    short_description: str | None
    likely_relevant: bool | None
    matched_keywords: tuple[str, ...]
    matched_locations: tuple[str, ...]
    current_status: str
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    first_seen_run_id: int | None
    last_seen_run_id: int | None
    discovery_status: str
    latest_score: float | None = None
    latest_priority: str | None = None
    latest_reason: str | None = None
    latest_concern: str | None = None
    latest_suggested_status: str | None = None


@dataclass(frozen=True)
class IngestionPersistSummary:
    ingestion_run_id: int
    fetched_count: int
    parsed_count: int
    unique_count: int
    new_count: int
    seen_again_count: int
    likely_relevant_count: int
    skipped_count: int = 0
    source_counts: dict[str, int] | MappingProxyType[str, int] = MappingProxyType({})
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnalysisBatchRecord:
    analysis_batch_id: int
    request_markdown_path: str
    request_json_path: str
    job_count: int


@dataclass(frozen=True)
class AnalysisImportSummary:
    imported_count: int = 0
    skipped_count: int = 0
    updated_statuses_count: int = 0


def _fetchone_id(conn, sql: str, params: tuple[Any, ...]) -> int:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        raise DatabaseError("Database operation did not return an id.")
    return int(row[0])


def _job_identity_values(job: ParsedJob) -> dict[str, str | None]:
    normalized_url = normalize_url(job.url)
    return {
        "normalized_url": normalized_url,
        "normalized_url_hash": hash_normalized_url(normalized_url),
        "normalized_title": normalize_text(job.title),
        "normalized_company": normalize_text(job.company) or None,
        "normalized_location": normalize_text(job.location) or None,
    }


def create_ingestion_run(conn, *, selected_user_id: str | None, mode: str) -> int:
    return _fetchone_id(
        conn,
        """
        INSERT INTO ingestion_runs (selected_user_id, mode, status)
        VALUES (%s, %s, 'started')
        RETURNING id
        """,
        (selected_user_id, mode),
    )


def complete_ingestion_run(conn, *, ingestion_run_id: int, summary: IngestionPersistSummary, status: str = "completed") -> None:
    conn.execute(
        """
        UPDATE ingestion_runs
        SET completed_at = now(),
            fetched_count = %s,
            parsed_count = %s,
            new_count = %s,
            duplicate_count = %s,
            filtered_count = %s,
            status = %s
        WHERE id = %s
        """,
        (
            summary.fetched_count,
            summary.parsed_count,
            summary.new_count,
            summary.parsed_count - summary.unique_count,
            summary.unique_count - summary.likely_relevant_count,
            status,
            ingestion_run_id,
        ),
    )


def fail_ingestion_run(conn, *, ingestion_run_id: int, error_message: str) -> None:
    conn.execute(
        """
        UPDATE ingestion_runs
        SET completed_at = now(), status = 'failed', error_message = %s
        WHERE id = %s
        """,
        (error_message[:1000], ingestion_run_id),
    )


def upsert_email_message(conn, *, content: EmailMessageContent) -> None:
    metadata = content.metadata
    conn.execute(
        """
        INSERT INTO email_messages (
            user_id, gmail_message_id, gmail_thread_id, source, sender, subject,
            received_at, snippet, body_hash
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id, gmail_message_id) DO UPDATE
        SET gmail_thread_id = EXCLUDED.gmail_thread_id,
            source = EXCLUDED.source,
            sender = EXCLUDED.sender,
            subject = EXCLUDED.subject,
            received_at = EXCLUDED.received_at,
            snippet = EXCLUDED.snippet,
            body_hash = EXCLUDED.body_hash
        """,
        (
            metadata.user_id,
            metadata.gmail_message_id,
            metadata.gmail_thread_id,
            metadata.source,
            metadata.sender,
            metadata.subject,
            metadata.received_at,
            metadata.snippet,
            content.body_hash or metadata.body_hash,
        ),
    )


def upsert_job(conn, *, job: ParsedJob) -> int:
    values = _job_identity_values(job)
    if values["normalized_url_hash"]:
        existing = conn.execute(
            "SELECT id FROM jobs WHERE source = %s AND normalized_url_hash = %s",
            (job.source, values["normalized_url_hash"]),
        ).fetchone()
    else:
        existing = conn.execute(
            """
            SELECT id FROM jobs
            WHERE source = %s
              AND normalized_title = %s
              AND COALESCE(normalized_company, '') = COALESCE(%s, '')
              AND COALESCE(normalized_location, '') = COALESCE(%s, '')
              AND normalized_url_hash IS NULL
            """,
            (
                job.source,
                values["normalized_title"],
                values["normalized_company"],
                values["normalized_location"],
            ),
        ).fetchone()

    if existing:
        job_id = int(existing[0])
        conn.execute(
            """
            UPDATE jobs
            SET last_seen_at = now(),
                title = %s,
                company = %s,
                location = %s,
                url = COALESCE(%s, url),
                normalized_url = COALESCE(%s, normalized_url),
                short_description = COALESCE(%s, short_description),
                updated_at = now()
            WHERE id = %s
            """,
            (
                job.title,
                job.company,
                job.location,
                job.url,
                values["normalized_url"],
                job.short_description,
                job_id,
            ),
        )
        return job_id

    return _fetchone_id(
        conn,
        """
        INSERT INTO jobs (
            source, title, company, location, url, normalized_url, normalized_url_hash,
            normalized_title, normalized_company, normalized_location, short_description
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            job.source,
            job.title,
            job.company,
            job.location,
            job.url,
            values["normalized_url"],
            values["normalized_url_hash"],
            values["normalized_title"],
            values["normalized_company"],
            values["normalized_location"],
            job.short_description,
        ),
    )


def upsert_user_job(
    conn,
    *,
    user_id: str,
    job_id: int,
    ingestion_run_id: int,
    result: JobFilterResult,
) -> bool:
    existing = conn.execute(
        "SELECT 1 FROM user_jobs WHERE user_id = %s AND job_id = %s",
        (user_id, job_id),
    ).fetchone()
    seen_as_new = existing is None

    if seen_as_new:
        conn.execute(
            """
            INSERT INTO user_jobs (
                user_id, job_id, status, likely_relevant, matched_keywords, matched_locations,
                exclusion_matches, relevance_reason, first_seen_run_id, last_seen_run_id
            )
            VALUES (%s, %s, 'new', %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                job_id,
                result.likely_relevant,
                list(result.matched_keywords),
                list(result.matched_locations),
                list(result.exclusion_matches),
                result.relevance_reason,
                ingestion_run_id,
                ingestion_run_id,
            ),
        )
    else:
        conn.execute(
            """
            UPDATE user_jobs
            SET likely_relevant = %s,
                matched_keywords = %s,
                matched_locations = %s,
                exclusion_matches = %s,
                relevance_reason = %s,
                last_seen_at = now(),
                last_seen_run_id = %s,
                updated_at = now()
            WHERE user_id = %s AND job_id = %s
            """,
            (
                result.likely_relevant,
                list(result.matched_keywords),
                list(result.matched_locations),
                list(result.exclusion_matches),
                result.relevance_reason,
                ingestion_run_id,
                user_id,
                job_id,
            ),
        )

    conn.execute(
        """
        INSERT INTO job_run_occurrences (ingestion_run_id, user_id, job_id, seen_as_new)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (ingestion_run_id, user_id, job_id) DO UPDATE
        SET seen_as_new = EXCLUDED.seen_as_new,
            seen_at = now()
        """,
        (ingestion_run_id, user_id, job_id, seen_as_new),
    )
    return seen_as_new


def latest_ingestion_run_id(conn, *, user_id: str) -> int | None:
    row = conn.execute(
        """
        SELECT id FROM ingestion_runs
        WHERE selected_user_id = %s AND status = 'completed'
        ORDER BY completed_at DESC NULLS LAST, started_at DESC, id DESC
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()
    return int(row[0]) if row else None


def select_jobs_for_analysis(
    conn,
    *,
    user_id: str,
    limit: int,
    status: str | None = None,
    run_id: int | None = None,
    since_days: int | None = None,
    new_in_run_only: bool = False,
    likely_relevant_only: bool = False,
    not_analyzed_only: bool = False,
) -> list[StoredJob]:
    params: list[Any] = [user_id]
    where = ["uj.user_id = %s"]
    join_occurrence = run_id is not None or new_in_run_only

    if status:
        where.append("uj.status = %s")
        params.append(status)
    if likely_relevant_only:
        where.append("uj.likely_relevant IS TRUE")
    if since_days is not None:
        where.append("uj.last_seen_at >= now() - (%s * interval '1 day')")
        params.append(since_days)
    if not_analyzed_only:
        where.append(
            """
            NOT EXISTS (
                SELECT 1 FROM codex_job_analyses cja
                WHERE cja.user_id = uj.user_id AND cja.job_id = uj.job_id
            )
            """
        )
    if run_id is not None:
        where.append("jro.ingestion_run_id = %s")
        params.append(run_id)
    if new_in_run_only:
        where.append("jro.seen_as_new IS TRUE")

    occurrence_join = (
        "JOIN job_run_occurrences jro ON jro.user_id = uj.user_id AND jro.job_id = uj.job_id"
        if join_occurrence
        else "LEFT JOIN job_run_occurrences jro ON jro.user_id = uj.user_id AND jro.job_id = uj.job_id AND jro.ingestion_run_id = uj.last_seen_run_id"
    )

    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT
            j.id, uj.user_id, j.title, j.company, j.location, j.source, j.url,
            j.short_description, uj.likely_relevant, uj.matched_keywords,
            uj.matched_locations, uj.status, uj.first_seen_at, uj.last_seen_at,
            uj.first_seen_run_id, uj.last_seen_run_id,
            CASE
                WHEN jro.seen_as_new IS TRUE THEN 'newly discovered in selected run'
                WHEN jro.ingestion_run_id IS NOT NULL THEN 'seen again'
                ELSE 'historical'
            END AS discovery_status,
            latest.score, latest.priority, latest.reason, latest.concern, latest.suggested_status
        FROM user_jobs uj
        JOIN jobs j ON j.id = uj.job_id
        {occurrence_join}
        LEFT JOIN LATERAL (
            SELECT score, priority, reason, concern, suggested_status
            FROM codex_job_analyses cja
            WHERE cja.user_id = uj.user_id AND cja.job_id = uj.job_id
            ORDER BY created_at DESC, id DESC
            LIMIT 1
        ) latest ON TRUE
        WHERE {" AND ".join(where)}
        ORDER BY uj.likely_relevant DESC NULLS LAST, uj.last_seen_at DESC, j.id DESC
        LIMIT %s
        """,
        tuple(params),
    ).fetchall()

    result: list[StoredJob] = []
    for row in rows:
        result.append(
            StoredJob(
                job_id=int(row[0]),
                user_id=str(row[1]),
                title=str(row[2]),
                company=row[3],
                location=row[4],
                source=str(row[5]),
                url=row[6],
                short_description=row[7],
                likely_relevant=row[8],
                matched_keywords=tuple(row[9] or ()),
                matched_locations=tuple(row[10] or ()),
                current_status=str(row[11]),
                first_seen_at=row[12],
                last_seen_at=row[13],
                first_seen_run_id=row[14],
                last_seen_run_id=row[15],
                discovery_status=str(row[16]),
                latest_score=float(row[17]) if row[17] is not None else None,
                latest_priority=row[18],
                latest_reason=row[19],
                latest_concern=row[20],
                latest_suggested_status=row[21],
            )
        )
    return result


def create_analysis_batch(
    conn,
    *,
    user_id: str,
    request_markdown_path: str,
    request_json_path: str,
    job_count: int,
) -> int:
    return _fetchone_id(
        conn,
        """
        INSERT INTO analysis_batches (user_id, request_markdown_path, request_json_path, job_count, status)
        VALUES (%s, %s, %s, %s, 'prepared')
        RETURNING id
        """,
        (user_id, request_markdown_path, request_json_path, job_count),
    )


def create_runtime_analysis_batch(
    conn,
    *,
    user_id: str,
    job_count: int,
) -> int:
    return _fetchone_id(
        conn,
        """
        INSERT INTO analysis_batches (user_id, job_count, status)
        VALUES (%s, %s, 'running')
        RETURNING id
        """,
        (user_id, job_count),
    )


def job_exists_for_user(conn, *, user_id: str, job_id: int) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM user_jobs WHERE user_id = %s AND job_id = %s",
            (user_id, job_id),
        ).fetchone()
        is not None
    )


def analysis_exists(conn, *, user_id: str, job_id: int, analysis_batch_id: int | None) -> bool:
    if analysis_batch_id is None:
        return (
            conn.execute(
                """
                SELECT 1 FROM codex_job_analyses
                WHERE user_id = %s AND job_id = %s
                """,
                (user_id, job_id),
            ).fetchone()
            is not None
        )
    return (
        conn.execute(
            """
            SELECT 1 FROM codex_job_analyses
            WHERE user_id = %s AND job_id = %s AND analysis_batch_id = %s
            """,
            (user_id, job_id, analysis_batch_id),
        ).fetchone()
        is not None
    )


def insert_analysis(
    conn,
    *,
    user_id: str,
    job_id: int,
    priority: str,
    score: float | None,
    reason: str | None,
    concern: str | None,
    suggested_status: str | None,
    analysis_batch_id: int | None,
    source_file: str,
    provider: str = "codex",
) -> None:
    conn.execute(
        """
        INSERT INTO codex_job_analyses (
            user_id, job_id, analysis_batch_id, score, priority, reason,
            concern, suggested_status, source_file, provider
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            user_id,
            job_id,
            analysis_batch_id,
            Decimal(str(score)) if score is not None else None,
            priority,
            reason,
            concern,
            suggested_status,
            source_file,
            provider,
        ),
    )


def update_user_job_status(conn, *, user_id: str, job_id: int, status: str) -> None:
    if status not in VALID_STATUSES:
        raise DatabaseError("Invalid status value.")
    conn.execute(
        """
        UPDATE user_jobs
        SET status = %s, updated_at = now()
        WHERE user_id = %s AND job_id = %s
        """,
        (status, user_id, job_id),
    )


def mark_analysis_batch_imported(conn, *, analysis_batch_id: int, result_json_path: str) -> None:
    conn.execute(
        """
        UPDATE analysis_batches
        SET status = 'imported', imported_at = now(), result_json_path = %s
        WHERE id = %s
        """,
        (result_json_path, analysis_batch_id),
    )


def mark_analysis_batch_completed(conn, *, analysis_batch_id: int) -> None:
    conn.execute(
        """
        UPDATE analysis_batches
        SET status = 'completed', imported_at = now(), error_message = NULL
        WHERE id = %s
        """,
        (analysis_batch_id,),
    )


def mark_analysis_batch_failed(conn, *, analysis_batch_id: int, error_message: str) -> None:
    conn.execute(
        """
        UPDATE analysis_batches
        SET status = 'failed', error_message = %s
        WHERE id = %s
        """,
        (error_message[:1000], analysis_batch_id),
    )
