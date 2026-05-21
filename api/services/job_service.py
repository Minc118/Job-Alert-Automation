from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from api.schemas import CodexJobAnalysisResponse, JobResponse, UserJobStatusResponse
from api.services.database import readonly_connection, write_connection
from api.services.run_service import get_latest_run
from api.services.user_service import validate_user_id
from job_alert_automation.repository import job_exists_for_user, update_user_job_status


def _datetime_to_string(value: Any) -> str:
    return value.isoformat(sep=" ", timespec="minutes") if value is not None else ""


def _discovery_from_row(seen_as_new: bool | None, occurrence_run_id: int | None, requested_run_id: int | None) -> str:
    if requested_run_id is None:
        return "historical"
    if occurrence_run_id is None:
        return "historical"
    if seen_as_new:
        return "new_in_this_run"
    return "seen_before"


def _row_to_job(row: Any, *, requested_run_id: int | None) -> JobResponse:
    score = float(row[18]) if row[18] is not None else None
    priority = row[19] or "Not analyzed"
    analysis = None
    if row[19] is not None or row[18] is not None or row[20] is not None or row[21] is not None:
        analysis = CodexJobAnalysisResponse(
            score=score,
            priority=str(priority),
            reason=row[20] or "",
            concern=row[21] or "",
            suggestedStatus=row[22],
            analyzedAt=_datetime_to_string(row[23]),
            analysisBatchId=row[24],
        )

    return JobResponse(
        id=int(row[0]),
        userId=str(row[1]),
        title=str(row[2]),
        company=row[3] or "",
        location=row[4] or "",
        source=str(row[5]),
        url=row[6] or "",
        shortDescription=row[7] or "",
        likelyRelevant=bool(row[8]),
        matchedKeywords=list(row[9] or []),
        matchedLocations=list(row[10] or []),
        exclusionMatches=list(row[11] or []),
        status=str(row[12]),
        discovery=_discovery_from_row(row[16], row[17], requested_run_id),
        firstSeenAt=_datetime_to_string(row[13]),
        lastSeenAt=_datetime_to_string(row[14]),
        lastSeenRunId=row[15],
        codexAnalysis=analysis,
    )


def _select_jobs(conn: Any, *, user_id: str, requested_run_id: int | None, limit: int) -> list[JobResponse]:
    run_join = (
        """
        LEFT JOIN job_run_occurrences jro
            ON jro.user_id = uj.user_id
           AND jro.job_id = uj.job_id
           AND jro.ingestion_run_id = %s
        """
        if requested_run_id is not None
        else """
        LEFT JOIN job_run_occurrences jro
            ON jro.user_id = uj.user_id
           AND jro.job_id = uj.job_id
           AND jro.ingestion_run_id = uj.last_seen_run_id
        """
    )
    where = ["uj.user_id = %s"]
    params: list[Any] = []
    if requested_run_id is not None:
        params.append(requested_run_id)
        where.append("jro.ingestion_run_id = %s")
    params.append(user_id)
    if requested_run_id is not None:
        params.append(requested_run_id)
    params.append(limit)

    rows = conn.execute(
        f"""
        SELECT
            j.id,
            uj.user_id,
            j.title,
            j.company,
            j.location,
            j.source,
            j.url,
            j.short_description,
            uj.likely_relevant,
            uj.matched_keywords,
            uj.matched_locations,
            uj.exclusion_matches,
            uj.status,
            uj.first_seen_at,
            uj.last_seen_at,
            uj.last_seen_run_id,
            jro.seen_as_new,
            jro.ingestion_run_id,
            latest.score,
            latest.priority,
            latest.reason,
            latest.concern,
            latest.suggested_status,
            latest.created_at,
            latest.analysis_batch_id
        FROM user_jobs uj
        JOIN jobs j ON j.id = uj.job_id
        {run_join}
        LEFT JOIN LATERAL (
            SELECT score, priority, reason, concern, suggested_status, created_at, analysis_batch_id
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
    return [_row_to_job(row, requested_run_id=requested_run_id) for row in rows]


def list_jobs(user_id: str, *, range_name: str = "latest_run", limit: int = 100) -> list[JobResponse]:
    validate_user_id(user_id)
    latest_run = get_latest_run(user_id) if range_name == "latest_run" else None
    requested_run_id = latest_run.id if latest_run else None
    with readonly_connection() as conn:
        return _select_jobs(conn, user_id=user_id, requested_run_id=requested_run_id, limit=limit)


def get_job(user_id: str, job_id: int) -> JobResponse:
    validate_user_id(user_id)
    with readonly_connection() as conn:
        jobs = _select_jobs(conn, user_id=user_id, requested_run_id=None, limit=500)
    for job in jobs:
        if job.id == job_id:
            return job
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found for selected user.")


def set_job_status(user_id: str, job_id: int, new_status: str) -> UserJobStatusResponse:
    validate_user_id(user_id)
    if new_status not in {"new", "saved", "applied", "ignored"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid status value.")

    with write_connection() as conn:
        if not job_exists_for_user(conn, user_id=user_id, job_id=job_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found for selected user.")
        update_user_job_status(conn, user_id=user_id, job_id=job_id, status=new_status)
        conn.commit()

    return UserJobStatusResponse(userId=user_id, jobId=job_id, status=new_status)  # type: ignore[arg-type]
