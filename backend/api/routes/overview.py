from __future__ import annotations

from fastapi import APIRouter, Query

from api.schemas import OverviewResponse
from api.services.overview_service import get_overview


router = APIRouter(prefix="/api", tags=["overview"])


@router.get("/overview", response_model=OverviewResponse)
def overview(user_id: str = Query(...), range: str = Query("latest_run")) -> OverviewResponse:
    return get_overview(user_id, range_name=range)
