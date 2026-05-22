from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.routes.me import optional_current_identity, resolve_request_user_id
from api.schemas import JobResponse, UserJobStatusResponse, UserJobStatusUpdate
from api.services.auth_service import VerifiedIdentity
from api.services.job_service import get_job, list_jobs, set_job_status


router = APIRouter(prefix="/api", tags=["jobs"])


@router.get("/jobs", response_model=list[JobResponse])
def get_jobs(
    user_id: str | None = Query(None),
    range: str = Query("latest_run"),
    limit: int = Query(100, ge=1, le=500),
    identity: VerifiedIdentity | None = Depends(optional_current_identity),
) -> list[JobResponse]:
    scoped_user_id, session_scoped = resolve_request_user_id(user_id, identity)
    return list_jobs(scoped_user_id, range_name=range, limit=limit, validate_config_user=not session_scoped)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_detail(
    job_id: int,
    user_id: str | None = Query(None),
    identity: VerifiedIdentity | None = Depends(optional_current_identity),
) -> JobResponse:
    scoped_user_id, session_scoped = resolve_request_user_id(user_id, identity)
    return get_job(scoped_user_id, job_id, validate_config_user=not session_scoped)


@router.patch("/user-jobs/{job_id}/status", response_model=UserJobStatusResponse)
def update_job_status(
    job_id: int,
    payload: UserJobStatusUpdate,
    identity: VerifiedIdentity | None = Depends(optional_current_identity),
) -> UserJobStatusResponse:
    scoped_user_id, session_scoped = resolve_request_user_id(payload.userId, identity)
    return set_job_status(scoped_user_id, job_id, payload.status, validate_config_user=not session_scoped)
