from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import ConfigError, PROJECT_ROOT, get_env_value, load_users_config
from .database import connect
from .repository import (
    AnalysisBatchRecord,
    AnalysisImportSummary,
    StoredJob,
    analysis_exists,
    create_analysis_batch,
    insert_analysis,
    job_exists_for_user,
    latest_ingestion_run_id,
    mark_analysis_batch_imported,
    select_jobs_for_analysis,
    update_user_job_status,
)


VALID_PRIORITIES = {"High", "Medium", "Low"}
VALID_SUGGESTED_STATUSES = {"new", "saved", "applied", "ignored"}
ANALYSIS_REQUEST_DIR = PROJECT_ROOT / "output" / "analysis_requests"


@dataclass(frozen=True)
class AnalysisFilters:
    limit: int = 20
    status: str | None = None
    latest_run: bool = False
    run_id: int | None = None
    since_days: int | None = None
    new_in_run_only: bool = False
    likely_relevant_only: bool = False
    not_analyzed_only: bool = False


@dataclass(frozen=True)
class ProfileContent:
    path: Path
    content: str
    warning: str | None = None


class AnalysisValidationError(RuntimeError):
    """Raised for safe, user-facing analysis JSON validation errors."""


def profile_path_for_user(user_id: str) -> Path:
    env_name = f"PROFILE_{user_id.upper()}_PATH"
    configured = get_env_value(env_name, default=f"private/profile_{user_id}.md")
    path = Path(configured).expanduser()
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def load_profile_content(user_id: str) -> ProfileContent:
    config = load_users_config()
    preferences = config.preferences[user_id]
    path = profile_path_for_user(user_id)
    if path.exists():
        return ProfileContent(path=path, content=path.read_text(encoding="utf-8"))

    warning = f"Private profile file not found at {path}. Falling back to non-secret config preferences."
    fallback = "\n".join(
        [
            warning,
            "",
            "Target role keywords:",
            ", ".join(preferences.target_role_keywords),
            "",
            "Preferred locations:",
            ", ".join(preferences.preferred_locations),
            "",
            "Excluded keywords:",
            ", ".join(preferences.excluded_keywords),
        ]
    )
    return ProfileContent(path=path, content=fallback, warning=warning)


def _datetime_value(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def stored_job_to_dict(job: StoredJob) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "user_id": job.user_id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "source": job.source,
        "url": job.url,
        "short_description": job.short_description,
        "likely_relevant": job.likely_relevant,
        "matched_keywords": list(job.matched_keywords),
        "matched_locations": list(job.matched_locations),
        "current_status": job.current_status,
        "first_seen_at": _datetime_value(job.first_seen_at),
        "last_seen_at": _datetime_value(job.last_seen_at),
        "first_seen_run_id": job.first_seen_run_id,
        "last_seen_run_id": job.last_seen_run_id,
        "discovery_status": job.discovery_status,
        "latest_analysis": {
            "score": job.latest_score,
            "priority": job.latest_priority,
            "reason": job.latest_reason,
            "concern": job.latest_concern,
            "suggested_status": job.latest_suggested_status,
        },
    }


def _scope_label(filters: AnalysisFilters, resolved_run_id: int | None) -> str:
    if filters.latest_run:
        return f"Latest Run / Run ID {resolved_run_id}" if resolved_run_id else "Latest Run / none found"
    if filters.run_id is not None:
        return f"Run ID {filters.run_id}"
    if filters.since_days is not None:
        return f"Last {filters.since_days} Days"
    return "All History"


def render_analysis_markdown(
    *,
    user_display_name: str,
    user_id: str,
    profile: ProfileContent,
    jobs: list[StoredJob],
    filters: AnalysisFilters,
    resolved_run_id: int | None,
) -> str:
    lines = [
        "# Codex Job Analysis Request",
        "",
        "User:",
        user_display_name,
        "",
        "Batch / Time Scope:",
        f"- {_scope_label(filters, resolved_run_id)}",
        f"- Newly discovered only: {'yes' if filters.new_in_run_only else 'no'}",
        f"- Status filter: {filters.status or 'all'}",
        f"- Likely relevant only: {'yes' if filters.likely_relevant_only else 'no'}",
        f"- Not analyzed only: {'yes' if filters.not_analyzed_only else 'no'}",
        "",
        "Profile:",
        profile.content,
        "",
        "Instructions for Codex:",
        "Please analyze the following job opportunities for this user.",
        "Rank them according to realistic application priority.",
        "Return structured JSON only.",
        "Do not call any external API.",
        "Do not invent missing job requirements.",
        "Be conservative and realistic.",
        "",
        "Scoring:",
        "- 9-10: very strong fit, should apply first",
        "- 7-8: good fit, should consider applying",
        "- 5-6: possible fit, apply only if capacity allows",
        "- 1-4: weak fit or unsuitable",
        "",
        "Output JSON format:",
        "```json",
        json.dumps(
            [
                {
                    "user_id": user_id,
                    "job_id": 123,
                    "score": 8.5,
                    "priority": "High",
                    "reason": "Short reason why this role fits the user's background.",
                    "concern": "Possible mismatch or point to check.",
                    "suggested_status": "saved",
                }
            ],
            indent=2,
        ),
        "```",
        "",
        "Jobs:",
    ]
    if not jobs:
        lines.append("No jobs matched the selected filters.")
    for index, job in enumerate(jobs, start=1):
        lines.extend(
            [
                "",
                f"## {index}. {job.title}",
                f"- job_id: {job.job_id}",
                f"- title: {job.title}",
                f"- company: {job.company or ''}",
                f"- location: {job.location or ''}",
                f"- source: {job.source}",
                f"- url: {job.url or ''}",
                f"- short_description: {job.short_description or ''}",
                f"- likely_relevant: {job.likely_relevant}",
                f"- matched_keywords: {', '.join(job.matched_keywords)}",
                f"- matched_locations: {', '.join(job.matched_locations)}",
                f"- current_status: {job.current_status}",
                f"- first_seen_at: {_datetime_value(job.first_seen_at) or ''}",
                f"- last_seen_at: {_datetime_value(job.last_seen_at) or ''}",
                f"- discovery status: {job.discovery_status}",
            ]
        )
    return "\n".join(lines) + "\n"


def _request_payload(
    *,
    analysis_batch_id: int | None,
    user_id: str,
    user_display_name: str,
    profile: ProfileContent,
    jobs: list[StoredJob],
    filters: AnalysisFilters,
    resolved_run_id: int | None,
) -> dict[str, Any]:
    return {
        "analysis_batch_id": analysis_batch_id,
        "user_id": user_id,
        "user_display_name": user_display_name,
        "scope": {
            "label": _scope_label(filters, resolved_run_id),
            "latest_run": filters.latest_run,
            "run_id": resolved_run_id if filters.latest_run else filters.run_id,
            "since_days": filters.since_days,
            "new_in_run_only": filters.new_in_run_only,
            "status": filters.status,
            "likely_relevant_only": filters.likely_relevant_only,
            "not_analyzed_only": filters.not_analyzed_only,
        },
        "profile": {
            "path": str(profile.path),
            "content": profile.content,
            "warning": profile.warning,
        },
        "instructions": {
            "return_structured_json_only": True,
            "do_not_call_external_api": True,
            "priority_values": ["High", "Medium", "Low"],
            "suggested_status_values": ["new", "saved", "applied", "ignored"],
        },
        "jobs": [stored_job_to_dict(job) for job in jobs],
    }


def prepare_analysis_request(
    database_url: str,
    *,
    user_id: str,
    filters: AnalysisFilters,
) -> AnalysisBatchRecord:
    config = load_users_config()
    config.validate_user_id(user_id)
    if filters.limit < 1:
        raise ConfigError("--limit must be at least 1.")
    if filters.status and filters.status not in VALID_SUGGESTED_STATUSES:
        raise ConfigError("--status must be one of: new, saved, applied, ignored.")
    if filters.run_id is not None and filters.latest_run:
        raise ConfigError("Use either --latest-run or --run-id, not both.")
    if filters.new_in_run_only and not filters.latest_run and filters.run_id is None:
        raise ConfigError("--new-in-run-only requires --latest-run or --run-id.")

    profile = load_profile_content(user_id)
    user = config.users[user_id]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ANALYSIS_REQUEST_DIR.mkdir(parents=True, exist_ok=True)
    timestamp_md = ANALYSIS_REQUEST_DIR / f"analysis_{user_id}_{timestamp}.md"
    timestamp_json = ANALYSIS_REQUEST_DIR / f"analysis_{user_id}_{timestamp}.json"
    latest_md = ANALYSIS_REQUEST_DIR / f"latest_{user_id}.md"
    latest_json = ANALYSIS_REQUEST_DIR / f"latest_{user_id}.json"

    with connect(database_url) as conn:
        resolved_run_id = latest_ingestion_run_id(conn, user_id=user_id) if filters.latest_run else filters.run_id
        if filters.latest_run and resolved_run_id is None:
            jobs = []
        else:
            jobs = select_jobs_for_analysis(
                conn,
                user_id=user_id,
                limit=filters.limit,
                status=filters.status,
                run_id=resolved_run_id,
                since_days=filters.since_days,
                new_in_run_only=filters.new_in_run_only,
                likely_relevant_only=filters.likely_relevant_only,
                not_analyzed_only=filters.not_analyzed_only,
            )

        markdown = render_analysis_markdown(
            user_display_name=user.display_name,
            user_id=user_id,
            profile=profile,
            jobs=jobs,
            filters=filters,
            resolved_run_id=resolved_run_id,
        )
        timestamp_md.write_text(markdown, encoding="utf-8")
        payload = _request_payload(
            analysis_batch_id=None,
            user_id=user_id,
            user_display_name=user.display_name,
            profile=profile,
            jobs=jobs,
            filters=filters,
            resolved_run_id=resolved_run_id,
        )
        timestamp_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        analysis_batch_id = create_analysis_batch(
            conn,
            user_id=user_id,
            request_markdown_path=_display_path(timestamp_md),
            request_json_path=_display_path(timestamp_json),
            job_count=len(jobs),
        )
        conn.commit()

    payload["analysis_batch_id"] = analysis_batch_id
    timestamp_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.copyfile(timestamp_md, latest_md)
    shutil.copyfile(timestamp_json, latest_json)
    return AnalysisBatchRecord(
        analysis_batch_id=analysis_batch_id,
        request_markdown_path=_display_path(latest_md),
        request_json_path=_display_path(latest_json),
        job_count=len(jobs),
    )


def _load_analysis_results(path: Path) -> tuple[int | None, str | None, list[dict[str, Any]]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return None, None, raw
    if isinstance(raw, dict):
        results = raw.get("results")
        if not isinstance(results, list):
            raise AnalysisValidationError("Analysis result JSON must contain a results list.")
        analysis_batch_id = raw.get("analysis_batch_id")
        user_id = raw.get("user_id")
        return (
            int(analysis_batch_id) if analysis_batch_id is not None else None,
            str(user_id) if user_id is not None else None,
            results,
        )
    raise AnalysisValidationError("Analysis result JSON must be an object or list.")


def _validate_result(item: dict[str, Any], default_user_id: str | None) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise AnalysisValidationError("Each analysis result must be an object.")
    user_id = item.get("user_id") or default_user_id
    if not isinstance(user_id, str) or not user_id:
        raise AnalysisValidationError("Each result must include user_id.")
    try:
        job_id = int(item["job_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise AnalysisValidationError("Each result must include a valid job_id.") from exc
    priority = item.get("priority")
    if priority not in VALID_PRIORITIES:
        raise AnalysisValidationError("priority must be one of: High, Medium, Low.")
    score = item.get("score")
    if score is not None:
        try:
            score = float(score)
        except (TypeError, ValueError) as exc:
            raise AnalysisValidationError("score must be numeric when provided.") from exc
        if score < 0 or score > 10:
            raise AnalysisValidationError("score must be between 0 and 10.")
    suggested_status = item.get("suggested_status")
    if suggested_status is not None and suggested_status not in VALID_SUGGESTED_STATUSES:
        raise AnalysisValidationError("suggested_status must be one of: new, saved, applied, ignored.")
    return {
        "user_id": user_id,
        "job_id": job_id,
        "score": score,
        "priority": priority,
        "reason": item.get("reason"),
        "concern": item.get("concern"),
        "suggested_status": suggested_status,
    }


def import_analysis_results(
    database_url: str,
    *,
    result_path: Path,
    overwrite: bool = False,
) -> AnalysisImportSummary:
    analysis_batch_id, default_user_id, raw_results = _load_analysis_results(result_path)
    validated = [_validate_result(item, default_user_id) for item in raw_results]
    config = load_users_config()

    imported = 0
    skipped = 0
    updated_statuses = 0
    with connect(database_url) as conn:
        for item in validated:
            config.validate_user_id(item["user_id"])
            if not job_exists_for_user(conn, user_id=item["user_id"], job_id=item["job_id"]):
                skipped += 1
                continue
            if not overwrite and analysis_exists(
                conn,
                user_id=item["user_id"],
                job_id=item["job_id"],
                analysis_batch_id=analysis_batch_id,
            ):
                skipped += 1
                continue
            insert_analysis(
                conn,
                user_id=item["user_id"],
                job_id=item["job_id"],
                priority=item["priority"],
                score=item["score"],
                reason=item["reason"],
                concern=item["concern"],
                suggested_status=item["suggested_status"],
                analysis_batch_id=analysis_batch_id,
                source_file=str(result_path),
            )
            imported += 1
            if item["suggested_status"] in VALID_SUGGESTED_STATUSES:
                update_user_job_status(
                    conn,
                    user_id=item["user_id"],
                    job_id=item["job_id"],
                    status=item["suggested_status"],
                )
                updated_statuses += 1
        if analysis_batch_id is not None:
            mark_analysis_batch_imported(conn, analysis_batch_id=analysis_batch_id, result_json_path=str(result_path))
        conn.commit()
    return AnalysisImportSummary(
        imported_count=imported,
        skipped_count=skipped,
        updated_statuses_count=updated_statuses,
    )
