from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from api.routes.me import optional_current_identity, resolve_request_user_id
from api.schemas import IngestionRunResponse
from api.services.auth_service import VerifiedIdentity
from api.services.run_service import list_runs


router = APIRouter(prefix="/api", tags=["runs"])


@router.get("/runs", response_model=list[IngestionRunResponse])
def get_runs(
    user_id: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    identity: VerifiedIdentity | None = Depends(optional_current_identity),
) -> list[IngestionRunResponse]:
    scoped_user_id, session_scoped = resolve_request_user_id(user_id, identity)
    return list_runs(scoped_user_id, limit=limit, validate_config_user=not session_scoped)
