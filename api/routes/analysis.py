from __future__ import annotations

from fastapi import APIRouter

from api.schemas import AnalysisImportCreate, AnalysisImportResponse, AnalysisRequestCreate, AnalysisRequestResponse
from api.services.analysis_service import create_analysis_request, import_analysis_result


router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analysis-requests", response_model=AnalysisRequestResponse)
def prepare_analysis_request_endpoint(payload: AnalysisRequestCreate) -> AnalysisRequestResponse:
    return create_analysis_request(payload)


@router.post("/analysis-import", response_model=AnalysisImportResponse)
def import_analysis_result_endpoint(payload: AnalysisImportCreate) -> AnalysisImportResponse:
    return import_analysis_result(payload)
