from __future__ import annotations

from typing import Any

from api.schemas import IngestionRunResponse
from api.services.database import readonly_connection
from api.services.user_service import validate_user_id


def _datetime_to_string(value: Any) -> str:
    return value.isoformat(sep=" ", timespec="minutes") if value is not None else ""


def _row_to_run(row: Any, user_id: str) -> IngestionRunResponse:
    return IngestionRunResponse(
        id=int(row[0]),
        userId=user_id,
        startedAt=_datetime_to_string(row[1]),
        completedAt=_datetime_to_string(row[2]),
        emailsFetched=int(row[3] or 0),
        jobsParsed=int(row[4] or 0),
        newlyDiscovered=int(row[5] or 0),
        seenAgain=int(row[6] or 0),
        duplicatesSkipped=int(row[7] or 0),
        likelyRelevant=int(row[8] or 0),
        codexAnalyzed=int(row[9] or 0),
    )


def list_runs(user_id: str, *, limit: int = 20) -> list[IngestionRunResponse]:
    validate_user_id(user_id)
    with readonly_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                ir.id,
                ir.started_at,
                ir.completed_at,
                ir.fetched_count,
                ir.parsed_count,
                COALESCE(SUM(CASE WHEN jro.seen_as_new THEN 1 ELSE 0 END), 0) AS newly_discovered,
                COALESCE(SUM(CASE WHEN jro.seen_as_new THEN 0 ELSE 1 END), 0) AS seen_again,
                ir.duplicate_count,
                COALESCE(SUM(CASE WHEN uj.likely_relevant THEN 1 ELSE 0 END), 0) AS likely_relevant,
                COUNT(DISTINCT cja.job_id) AS codex_analyzed
            FROM ingestion_runs ir
            LEFT JOIN job_run_occurrences jro
                ON jro.ingestion_run_id = ir.id AND jro.user_id = ir.selected_user_id
            LEFT JOIN user_jobs uj
                ON uj.user_id = jro.user_id AND uj.job_id = jro.job_id
            LEFT JOIN codex_job_analyses cja
                ON cja.user_id = jro.user_id AND cja.job_id = jro.job_id
            WHERE ir.selected_user_id = %s
            GROUP BY ir.id
            ORDER BY ir.completed_at DESC NULLS LAST, ir.started_at DESC, ir.id DESC
            LIMIT %s
            """,
            (user_id, limit),
        ).fetchall()
    return [_row_to_run(row, user_id) for row in rows]


def get_latest_run(user_id: str) -> IngestionRunResponse | None:
    runs = list_runs(user_id, limit=1)
    return runs[0] if runs else None
