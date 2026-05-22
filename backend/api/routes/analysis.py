from __future__ import annotations

from fastapi import APIRouter, Depends

from api.routes.me import verify_current_identity
from api.schemas import (
    AnalysisImportCreate,
    AnalysisImportResponse,
    AnalysisRequestCreate,
    AnalysisRequestResponse,
    AnalysisRunCreate,
    AnalysisRunResponse,
)
from api.services.analysis_service import create_analysis_request, import_analysis_result
from api.services.auth_service import VerifiedIdentity, get_or_create_app_profile
from api.services.gemini_analysis_service import run_gemini_analysis


router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analysis-requests", response_model=AnalysisRequestResponse)
def prepare_analysis_request_endpoint(payload: AnalysisRequestCreate) -> AnalysisRequestResponse:
    return create_analysis_request(payload)


@router.post("/analysis-import", response_model=AnalysisImportResponse)
def import_analysis_result_endpoint(payload: AnalysisImportCreate) -> AnalysisImportResponse:
    return import_analysis_result(payload)


@router.post("/analysis/run", response_model=AnalysisRunResponse)
def run_gemini_analysis_endpoint(
    payload: AnalysisRunCreate,
    identity: VerifiedIdentity = Depends(verify_current_identity),
) -> AnalysisRunResponse:
    profile = get_or_create_app_profile(identity)
    return run_gemini_analysis(profile.user.id, payload)
