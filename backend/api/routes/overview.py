from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.routes.me import optional_current_identity, resolve_request_user_id
from api.schemas import OverviewResponse
from api.services.auth_service import VerifiedIdentity
from api.services.overview_service import get_overview


router = APIRouter(prefix="/api", tags=["overview"])


@router.get("/overview", response_model=OverviewResponse)
def overview(
    user_id: str | None = Query(None),
    range: str = Query("latest_run"),
    identity: VerifiedIdentity | None = Depends(optional_current_identity),
) -> OverviewResponse:
    scoped_user_id, session_scoped = resolve_request_user_id(user_id, identity)
    return get_overview(scoped_user_id, range_name=range, validate_config_user=not session_scoped)
