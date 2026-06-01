from __future__ import annotations

from collections import Counter

from api.schemas import OverviewResponse
from api.services.job_service import list_jobs
from api.services.run_service import get_latest_run
from api.services.user_service import validate_user_id


def get_overview(user_id: str, *, range_name: str = "latest_run", validate_config_user: bool = True) -> OverviewResponse:
    if validate_config_user:
        validate_user_id(user_id)
    jobs = list_jobs(user_id, range_name=range_name, limit=100, validate_config_user=validate_config_user)
    latest_run = get_latest_run(user_id, validate_config_user=validate_config_user)
    source_counts = Counter(job.source for job in jobs)
    top_jobs = sorted(
        [job for job in jobs if job.codexAnalysis and job.codexAnalysis.priority in {"High", "Medium"}],
        key=lambda job: job.codexAnalysis.score if job.codexAnalysis and job.codexAnalysis.score is not None else 0,
        reverse=True,
    )[:5]

    metrics = {
        "newJobs": sum(1 for job in jobs if job.status == "new"),
        "newlyDiscovered": sum(1 for job in jobs if job.discovery == "new_in_this_run"),
        "likelyRelevant": sum(1 for job in jobs if job.likelyRelevant),
        "codexHighPriority": sum(1 for job in jobs if job.codexAnalysis and job.codexAnalysis.priority == "High"),
        "saved": sum(1 for job in jobs if job.status == "saved"),
        "applied": sum(1 for job in jobs if job.status == "applied"),
        "ignored": sum(1 for job in jobs if job.status == "ignored"),
    }

    recent_activity = []
    if latest_run:
        recent_activity.append({"label": "Latest job fetch completed", "time": latest_run.completedAt})
    if top_jobs:
        recent_activity.append({"label": "Latest AI analysis available", "time": top_jobs[0].codexAnalysis.analyzedAt or ""})

    return OverviewResponse(
        userId=user_id,
        range=range_name,
        metrics=metrics,
        latestRun=latest_run,
        sourceSummary=dict(source_counts),
        topRecommendedJobs=top_jobs,
        recentActivity=recent_activity,
    )
