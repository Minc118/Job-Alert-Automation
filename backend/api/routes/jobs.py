from __future__ import annotations

from fastapi import APIRouter, Query

from api.schemas import JobResponse, UserJobStatusResponse, UserJobStatusUpdate
from api.services.job_service import get_job, list_jobs, set_job_status


router = APIRouter(prefix="/api", tags=["jobs"])


@router.get("/jobs", response_model=list[JobResponse])
def get_jobs(
    user_id: str = Query(...),
    range: str = Query("latest_run"),
    limit: int = Query(100, ge=1, le=500),
) -> list[JobResponse]:
    return list_jobs(user_id, range_name=range, limit=limit)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_detail(job_id: int, user_id: str = Query(...)) -> JobResponse:
    return get_job(user_id, job_id)


@router.patch("/user-jobs/{job_id}/status", response_model=UserJobStatusResponse)
def update_job_status(job_id: int, payload: UserJobStatusUpdate) -> UserJobStatusResponse:
    return set_job_status(payload.userId, job_id, payload.status)
