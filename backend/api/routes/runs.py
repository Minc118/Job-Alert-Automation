from __future__ import annotations

from fastapi import APIRouter, Query

from api.schemas import IngestionRunResponse
from api.services.run_service import list_runs


router = APIRouter(prefix="/api", tags=["runs"])


@router.get("/runs", response_model=list[IngestionRunResponse])
def get_runs(user_id: str = Query(...), limit: int = Query(20, ge=1, le=100)) -> list[IngestionRunResponse]:
    return list_runs(user_id, limit=limit)
