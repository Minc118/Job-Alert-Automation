from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, status

from api.schemas import AnalysisImportCreate, AnalysisImportResponse, AnalysisRequestCreate, AnalysisRequestResponse
from api.services.database import require_database_url
from api.services.user_service import validate_user_id
from job_alert_automation.analysis import AnalysisFilters, AnalysisValidationError, import_analysis_results, prepare_analysis_request
from job_alert_automation.config import ConfigError, PROJECT_ROOT
from job_alert_automation.database import DatabaseError


ANALYSIS_RESULTS_DIR = PROJECT_ROOT / "output" / "analysis_results"


def create_analysis_request(payload: AnalysisRequestCreate) -> AnalysisRequestResponse:
    validate_user_id(payload.userId)
    if payload.limit < 1:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="limit must be at least 1.")
    database_url = require_database_url()
    filters = AnalysisFilters(
        limit=payload.limit,
        status=payload.status,
        latest_run=payload.latestRun,
        run_id=payload.runId,
        since_days=payload.sinceDays,
        new_in_run_only=payload.newInRunOnly,
        likely_relevant_only=payload.likelyRelevantOnly,
        not_analyzed_only=payload.notAnalyzedOnly,
    )

    try:
        record = prepare_analysis_request(database_url, user_id=payload.userId, filters=filters)
    except ConfigError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Check local configuration and network access.",
        ) from exc

    return AnalysisRequestResponse(
        analysisBatchId=record.analysis_batch_id,
        userId=payload.userId,
        jobCount=record.job_count,
        requestMarkdownPath=record.request_markdown_path,
        requestJsonPath=record.request_json_path,
        message="Analysis request prepared. Open the Markdown file in Codex manually.",
    )


def _safe_analysis_result_path(result_path: str) -> Path:
    if not result_path.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="resultPath is required.")

    raw_path = Path(result_path).expanduser()
    candidate = raw_path if raw_path.is_absolute() else PROJECT_ROOT / raw_path
    resolved = candidate.resolve()
    allowed_dir = ANALYSIS_RESULTS_DIR.resolve()

    if not resolved.is_relative_to(allowed_dir):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis result path must be inside output/analysis_results.",
        )
    if resolved.suffix.lower() != ".json":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Analysis result path must be a JSON file.")
    if not resolved.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis result file was not found.")

    return resolved.relative_to(PROJECT_ROOT)


def import_analysis_result(payload: AnalysisImportCreate) -> AnalysisImportResponse:
    result_path = _safe_analysis_result_path(payload.resultPath)
    database_url = require_database_url()

    try:
        summary = import_analysis_results(database_url, result_path=result_path, overwrite=payload.overwrite)
    except AnalysisValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ConfigError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DatabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Check local configuration and network access.",
        ) from exc

    return AnalysisImportResponse(
        importedCount=summary.imported_count,
        skippedCount=summary.skipped_count,
        updatedStatusesCount=summary.updated_statuses_count,
        resultPath=str(result_path),
        message="Analysis result imported. No AI API was called.",
    )
