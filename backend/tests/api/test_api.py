from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app
from api.schemas import (
    AnalysisImportResponse,
    AnalysisRequestResponse,
    AnalysisRunResponse,
    AppUserProfileResponse,
    GmailConnectionStatusResponse,
    UserJobStatusResponse,
    UserDocumentResponse,
    UserPreferencesResponse,
)
from api.services.auth_service import AuthenticatedAppProfile, VerifiedIdentity


def test_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_explicit_frontend_origin(monkeypatch) -> None:
    monkeypatch.setenv("API_CORS_ALLOWED_ORIGINS", "https://dashboard.example.test")
    client = TestClient(create_app())

    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://dashboard.example.test",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://dashboard.example.test"


def test_me_endpoint_requires_authentication() -> None:
    client = TestClient(create_app())

    response = client.get("/api/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


def test_me_endpoint_returns_verified_identity(monkeypatch) -> None:
    import api.routes.me as me_route

    app = create_app()
    app.dependency_overrides[me_route.verify_current_identity] = lambda: VerifiedIdentity(
        subject="auth-user-123",
        display_name="Signed In User",
        email="signed-in@example.test",
    )
    monkeypatch.setattr(
        me_route,
        "get_or_create_app_profile",
        lambda _identity: AuthenticatedAppProfile(
            user=AppUserProfileResponse(id="auth_profile_123", displayName="Signed In User"),
            onboarding_complete=False,
        ),
    )
    client = TestClient(app)

    response = client.get("/api/me")

    assert response.status_code == 200
    assert response.json() == {
        "authenticated": True,
        "authProvider": "neon",
        "user": {
            "subject": "auth-user-123",
            "displayName": "Signed In User",
            "email": "signed-in@example.test",
        },
        "appUser": {"id": "auth_profile_123", "displayName": "Signed In User"},
        "accountDataReady": True,
        "onboardingComplete": False,
    }


def test_jobs_endpoint_uses_session_scoped_user_without_user_query(monkeypatch) -> None:
    import api.routes.jobs as jobs_route
    import api.routes.me as me_route

    calls: list[tuple[str, bool]] = []

    monkeypatch.setattr(
        me_route,
        "get_or_create_app_profile",
        lambda _identity: AuthenticatedAppProfile(
            user=AppUserProfileResponse(id="auth_profile_123", displayName="Signed In User"),
            onboarding_complete=False,
        ),
    )
    monkeypatch.setattr(
        jobs_route,
        "list_jobs",
        lambda user_id, *, range_name, limit, validate_config_user: calls.append((user_id, validate_config_user)) or [],
    )
    app = create_app()
    app.dependency_overrides[me_route.optional_current_identity] = lambda: VerifiedIdentity(
        subject="auth-user-123",
        display_name="Signed In User",
        email="signed-in@example.test",
    )
    client = TestClient(app)

    response = client.get("/api/jobs?range=latest_run")

    assert response.status_code == 200
    assert response.json() == []
    assert calls == [("auth_profile_123", False)]


def test_preferences_endpoint_updates_session_scoped_preferences(monkeypatch) -> None:
    import api.routes.users as users_route

    calls: list[tuple[str, list[str], list[str], list[str]]] = []
    profile = AuthenticatedAppProfile(
        user=AppUserProfileResponse(id="auth_profile_123", displayName="Signed In User"),
        onboarding_complete=False,
    )
    monkeypatch.setattr(users_route, "get_or_create_app_profile", lambda _identity: profile)

    def fake_update_preferences(user_id, payload):
        calls.append((user_id, payload.targetRoleKeywords, payload.preferredLocations, payload.excludedKeywords))
        return UserPreferencesResponse(
            userId=user_id,
            targetRoleKeywords=payload.targetRoleKeywords,
            preferredLocations=payload.preferredLocations,
            excludedKeywords=payload.excludedKeywords,
            sourceQueries={},
        )

    monkeypatch.setattr(users_route, "update_preferences", fake_update_preferences)
    app = create_app()
    app.dependency_overrides[users_route.verify_current_identity] = lambda: VerifiedIdentity(
        subject="auth-user-123",
        display_name="Signed In User",
        email="signed-in@example.test",
    )
    client = TestClient(app)

    response = client.patch(
        "/api/user/preferences",
        json={
            "targetRoleKeywords": ["Werkstudent AI"],
            "preferredLocations": ["Berlin"],
            "excludedKeywords": ["senior"],
        },
    )

    assert response.status_code == 200
    assert response.json()["userId"] == "auth_profile_123"
    assert calls == [("auth_profile_123", ["Werkstudent AI"], ["Berlin"], ["senior"])]


def test_onboarding_complete_uses_verified_identity(monkeypatch) -> None:
    import api.routes.users as users_route

    monkeypatch.setattr(
        users_route,
        "complete_onboarding",
        lambda _identity: AuthenticatedAppProfile(
            user=AppUserProfileResponse(id="auth_profile_123", displayName="Signed In User"),
            onboarding_complete=True,
        ),
    )
    app = create_app()
    app.dependency_overrides[users_route.verify_current_identity] = lambda: VerifiedIdentity(
        subject="auth-user-123",
        display_name="Signed In User",
        email="signed-in@example.test",
    )
    client = TestClient(app)

    response = client.post("/api/onboarding/complete")

    assert response.status_code == 200
    assert response.json() == {"userId": "auth_profile_123", "onboardingComplete": True}


def test_gmail_status_uses_verified_identity(monkeypatch) -> None:
    import api.routes.gmail as gmail_route

    profile = AuthenticatedAppProfile(
        user=AppUserProfileResponse(id="auth_profile_123", displayName="Signed In User"),
        onboarding_complete=True,
    )
    monkeypatch.setattr(gmail_route, "get_or_create_app_profile", lambda _identity: profile)
    monkeypatch.setattr(
        gmail_route,
        "get_connection_status",
        lambda user_id: GmailConnectionStatusResponse(
            status="connected",
            connectedEmail=f"{user_id}@example.test",
            lastFetchAt=None,
            scope="https://www.googleapis.com/auth/gmail.readonly",
            detectedSources=["LinkedIn", "StepStone", "Indeed"],
        ),
    )
    app = create_app()
    app.dependency_overrides[gmail_route.verify_current_identity] = lambda: VerifiedIdentity(
        subject="auth-user-123",
        display_name="Signed In User",
        email="signed-in@example.test",
    )
    client = TestClient(app)

    response = client.get("/api/gmail/status")

    assert response.status_code == 200
    assert response.json()["connectedEmail"] == "auth_profile_123@example.test"
    assert response.json()["status"] == "connected"


def test_gmail_connect_returns_authorization_url_for_verified_identity(monkeypatch) -> None:
    import api.routes.gmail as gmail_route

    calls: list[str] = []
    profile = AuthenticatedAppProfile(
        user=AppUserProfileResponse(id="auth_profile_123", displayName="Signed In User"),
        onboarding_complete=True,
    )
    monkeypatch.setattr(gmail_route, "get_or_create_app_profile", lambda _identity: profile)
    monkeypatch.setattr(
        gmail_route,
        "create_authorization_url",
        lambda user_id: calls.append(user_id) or "https://accounts.google.test/oauth",
    )
    app = create_app()
    app.dependency_overrides[gmail_route.verify_current_identity] = lambda: VerifiedIdentity(
        subject="auth-user-123",
        display_name="Signed In User",
        email="signed-in@example.test",
    )
    client = TestClient(app)

    response = client.post("/api/gmail/connect")

    assert response.status_code == 200
    assert response.json() == {"authorizationUrl": "https://accounts.google.test/oauth"}
    assert calls == ["auth_profile_123"]


def test_gmail_disconnect_uses_verified_identity(monkeypatch) -> None:
    import api.routes.gmail as gmail_route

    calls: list[str] = []
    profile = AuthenticatedAppProfile(
        user=AppUserProfileResponse(id="auth_profile_123", displayName="Signed In User"),
        onboarding_complete=True,
    )
    monkeypatch.setattr(gmail_route, "get_or_create_app_profile", lambda _identity: profile)
    monkeypatch.setattr(
        gmail_route,
        "disconnect_gmail",
        lambda user_id: calls.append(user_id)
        or GmailConnectionStatusResponse(
            status="not_connected",
            connectedEmail=None,
            lastFetchAt=None,
            scope="https://www.googleapis.com/auth/gmail.readonly",
            detectedSources=["LinkedIn", "StepStone", "Indeed"],
        ),
    )
    app = create_app()
    app.dependency_overrides[gmail_route.verify_current_identity] = lambda: VerifiedIdentity(
        subject="auth-user-123",
        display_name="Signed In User",
        email="signed-in@example.test",
    )
    client = TestClient(app)

    response = client.post("/api/gmail/disconnect")

    assert response.status_code == 200
    assert response.json()["status"] == "not_connected"
    assert calls == ["auth_profile_123"]


def test_gmail_fetch_uses_verified_identity(monkeypatch) -> None:
    import api.routes.gmail as gmail_route
    from api.schemas import GmailFetchResponse

    calls: list[tuple[str, int]] = []
    profile = AuthenticatedAppProfile(
        user=AppUserProfileResponse(id="auth_profile_123", displayName="Signed In User"),
        onboarding_complete=True,
    )
    monkeypatch.setattr(gmail_route, "get_or_create_app_profile", lambda _identity: profile)
    monkeypatch.setattr(
        gmail_route,
        "run_connected_gmail_fetch",
        lambda user_id, *, max_results_per_source: calls.append((user_id, max_results_per_source))
        or GmailFetchResponse(
            ingestionRunId=12,
            emailsFetched=3,
            jobsParsed=4,
            uniqueJobs=4,
            newlyDiscovered=2,
            seenAgain=2,
            likelyRelevant=3,
        ),
    )
    app = create_app()
    app.dependency_overrides[gmail_route.verify_current_identity] = lambda: VerifiedIdentity(
        subject="auth-user-123",
        display_name="Signed In User",
        email="signed-in@example.test",
    )
    client = TestClient(app)

    response = client.post("/api/gmail/fetch?max_results_per_source=7")

    assert response.status_code == 200
    assert response.json()["ingestionRunId"] == 12
    assert response.json()["newlyDiscovered"] == 2
    assert calls == [("auth_profile_123", 7)]


def test_gemini_analysis_run_uses_verified_identity(monkeypatch) -> None:
    import api.routes.analysis as analysis_route

    calls: list[tuple[str, list[int]]] = []
    profile = AuthenticatedAppProfile(
        user=AppUserProfileResponse(id="auth_profile_123", displayName="Signed In User"),
        onboarding_complete=True,
    )
    monkeypatch.setattr(analysis_route, "get_or_create_app_profile", lambda _identity: profile)
    monkeypatch.setattr(
        analysis_route,
        "run_gemini_analysis",
        lambda user_id, payload: calls.append((user_id, payload.jobIds))
        or AnalysisRunResponse(
            analysisBatchId=27,
            userId=user_id,
            provider="gemini",
            model="gemini-2.5-flash",
            requestedCount=2,
            analyzedCount=2,
            skippedCount=0,
            message="done",
        ),
    )
    app = create_app()
    app.dependency_overrides[analysis_route.verify_current_identity] = lambda: VerifiedIdentity(
        subject="auth-user-123",
        display_name="Signed In User",
        email="signed-in@example.test",
    )
    client = TestClient(app)

    response = client.post("/api/analysis/run", json={"jobIds": [41, 42]})

    assert response.status_code == 200
    assert response.json()["provider"] == "gemini"
    assert calls == [("auth_profile_123", [41, 42])]


def test_documents_endpoint_uses_verified_identity(monkeypatch) -> None:
    import api.routes.documents as documents_route

    calls: list[str] = []
    profile = AuthenticatedAppProfile(
        user=AppUserProfileResponse(id="auth_profile_123", displayName="Signed In User"),
        onboarding_complete=True,
    )
    monkeypatch.setattr(documents_route, "get_or_create_app_profile", lambda _identity: profile)
    monkeypatch.setattr(
        documents_route,
        "list_documents",
        lambda user_id: calls.append(user_id)
        or [
            UserDocumentResponse(
                id=8,
                userId=user_id,
                documentType="profile_markdown",
                originalFilename="profile.md",
                mimeType="text/markdown",
                fileSizeBytes=42,
                isActive=True,
                createdAt="2026-05-22 09:00:00",
            )
        ],
    )
    app = create_app()
    app.dependency_overrides[documents_route.verify_current_identity] = lambda: VerifiedIdentity(
        subject="auth-user-123",
        display_name="Signed In User",
        email="signed-in@example.test",
    )
    client = TestClient(app)

    response = client.get("/api/user/documents")

    assert response.status_code == 200
    assert response.json()[0]["originalFilename"] == "profile.md"
    assert calls == ["auth_profile_123"]


def test_document_upload_uses_verified_identity(monkeypatch) -> None:
    import api.routes.documents as documents_route

    calls: list[tuple[str, str, str | None]] = []
    profile = AuthenticatedAppProfile(
        user=AppUserProfileResponse(id="auth_profile_123", displayName="Signed In User"),
        onboarding_complete=True,
    )
    monkeypatch.setattr(documents_route, "get_or_create_app_profile", lambda _identity: profile)

    async def fake_store_document_upload(user_id, *, document_type, upload):
        calls.append((user_id, document_type, upload.filename))
        return UserDocumentResponse(
            id=9,
            userId=user_id,
            documentType=document_type,
            originalFilename=upload.filename or "profile.md",
            mimeType="text/markdown",
            fileSizeBytes=18,
            isActive=True,
            createdAt="2026-05-22 09:00:00",
        )

    monkeypatch.setattr(documents_route, "store_document_upload", fake_store_document_upload)
    app = create_app()
    app.dependency_overrides[documents_route.verify_current_identity] = lambda: VerifiedIdentity(
        subject="auth-user-123",
        display_name="Signed In User",
        email="signed-in@example.test",
    )
    client = TestClient(app)

    response = client.post(
        "/api/user/documents",
        data={"documentType": "profile_markdown"},
        files={"file": ("profile.md", b"# Profile", "text/markdown")},
    )

    assert response.status_code == 200
    assert response.json()["documentType"] == "profile_markdown"
    assert calls == [("auth_profile_123", "profile_markdown", "profile.md")]


def test_me_endpoint_missing_jwks_url_is_safe(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("NEON_AUTH_JWKS_URL", raising=False)
    import job_alert_automation.config as config_module

    monkeypatch.setattr(config_module, "DEFAULT_ENV_PATH", tmp_path / ".env")
    client = TestClient(create_app())

    response = client.get("/api/me", headers={"Authorization": "Bearer placeholder.token.value"})

    assert response.status_code == 503
    assert "NEON_AUTH_JWKS_URL" in response.json()["detail"]
    assert "placeholder.token.value" not in response.text


def test_users_endpoint_uses_config_without_database(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import job_alert_automation.config as config_module

    monkeypatch.setattr(config_module, "DEFAULT_ENV_PATH", tmp_path / ".env")
    client = TestClient(create_app())

    response = client.get("/api/users")

    assert response.status_code == 200
    payload = response.json()
    assert {user["id"] for user in payload} == {"minjian", "chang"}


def test_jobs_endpoint_missing_database_url_is_safe(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import job_alert_automation.config as config_module

    monkeypatch.setattr(config_module, "DEFAULT_ENV_PATH", tmp_path / ".env")
    client = TestClient(create_app())

    response = client.get("/api/jobs?user_id=minjian&range=latest_run")

    assert response.status_code == 503
    assert "DATABASE_URL" in response.json()["detail"]
    assert "postgres://" not in response.text
    assert "postgresql://" not in response.text


def test_overview_endpoint_missing_database_url_is_safe(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import job_alert_automation.config as config_module

    monkeypatch.setattr(config_module, "DEFAULT_ENV_PATH", tmp_path / ".env")
    client = TestClient(create_app())

    response = client.get("/api/overview?user_id=minjian&range=latest_run")

    assert response.status_code == 503
    assert "DATABASE_URL" in response.json()["detail"]
    assert "postgres://" not in response.text
    assert "postgresql://" not in response.text


def test_invalid_user_is_safe(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import job_alert_automation.config as config_module

    monkeypatch.setattr(config_module, "DEFAULT_ENV_PATH", tmp_path / ".env")
    client = TestClient(create_app())

    response = client.get("/api/jobs?user_id=partner&range=latest_run")

    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown or invalid user."


def test_status_update_dispatches_service(monkeypatch) -> None:
    import api.routes.jobs as jobs_route

    calls: list[tuple[str, int, str]] = []

    def fake_set_job_status(
        user_id: str,
        job_id: int,
        status: str,
        *,
        validate_config_user: bool = True,
    ) -> UserJobStatusResponse:
        calls.append((user_id, job_id, status))
        return UserJobStatusResponse(userId=user_id, jobId=job_id, status=status)  # type: ignore[arg-type]

    monkeypatch.setattr(jobs_route, "set_job_status", fake_set_job_status)
    client = TestClient(create_app())

    response = client.patch("/api/user-jobs/123/status", json={"userId": "minjian", "status": "saved"})

    assert response.status_code == 200
    assert response.json() == {"userId": "minjian", "jobId": 123, "status": "saved"}
    assert calls == [("minjian", 123, "saved")]


def test_status_update_rejects_invalid_status() -> None:
    client = TestClient(create_app())

    response = client.patch("/api/user-jobs/123/status", json={"userId": "minjian", "status": "maybe"})

    assert response.status_code == 422


def test_status_update_missing_database_url_is_safe(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import job_alert_automation.config as config_module

    monkeypatch.setattr(config_module, "DEFAULT_ENV_PATH", tmp_path / ".env")
    client = TestClient(create_app())

    response = client.patch("/api/user-jobs/123/status", json={"userId": "minjian", "status": "saved"})

    assert response.status_code == 503
    assert "DATABASE_URL" in response.json()["detail"]
    assert "postgres://" not in response.text
    assert "postgresql://" not in response.text


def test_prepare_analysis_request_dispatches_service(monkeypatch) -> None:
    import api.routes.analysis as analysis_route

    calls: list[dict[str, object]] = []

    def fake_create_analysis_request(payload) -> AnalysisRequestResponse:
        calls.append(payload.model_dump())
        return AnalysisRequestResponse(
            analysisBatchId=77,
            userId=payload.userId,
            jobCount=3,
            requestMarkdownPath="output/analysis_requests/latest_minjian.md",
            requestJsonPath="output/analysis_requests/latest_minjian.json",
            message="prepared",
        )

    monkeypatch.setattr(analysis_route, "create_analysis_request", fake_create_analysis_request)
    client = TestClient(create_app())

    response = client.post(
        "/api/analysis-requests",
        json={"userId": "minjian", "limit": 20, "latestRun": True, "newInRunOnly": True},
    )

    assert response.status_code == 200
    assert response.json()["analysisBatchId"] == 77
    assert response.json()["requestMarkdownPath"] == "output/analysis_requests/latest_minjian.md"
    assert calls[0]["userId"] == "minjian"
    assert calls[0]["newInRunOnly"] is True


def test_prepare_analysis_missing_database_url_is_safe(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import job_alert_automation.config as config_module

    monkeypatch.setattr(config_module, "DEFAULT_ENV_PATH", tmp_path / ".env")
    client = TestClient(create_app())

    response = client.post("/api/analysis-requests", json={"userId": "minjian"})

    assert response.status_code == 503
    assert "DATABASE_URL" in response.json()["detail"]
    assert "postgres://" not in response.text
    assert "postgresql://" not in response.text


def test_import_analysis_dispatches_service(monkeypatch) -> None:
    import api.routes.analysis as analysis_route

    calls: list[dict[str, object]] = []

    def fake_import_analysis_result(payload) -> AnalysisImportResponse:
        calls.append(payload.model_dump())
        return AnalysisImportResponse(
            importedCount=2,
            skippedCount=1,
            updatedStatusesCount=1,
            resultPath=payload.resultPath,
            message="imported",
        )

    monkeypatch.setattr(analysis_route, "import_analysis_result", fake_import_analysis_result)
    client = TestClient(create_app())

    response = client.post(
        "/api/analysis-import",
        json={"resultPath": "output/analysis_results/latest_minjian_result.json", "overwrite": True},
    )

    assert response.status_code == 200
    assert response.json()["importedCount"] == 2
    assert response.json()["updatedStatusesCount"] == 1
    assert calls == [{"resultPath": "output/analysis_results/latest_minjian_result.json", "overwrite": True}]


def test_import_analysis_rejects_path_outside_results_dir() -> None:
    client = TestClient(create_app())

    response = client.post("/api/analysis-import", json={"resultPath": ".env"})

    assert response.status_code == 400
    assert "output/analysis_results" in response.json()["detail"]
    assert "postgres://" not in response.text
    assert "postgresql://" not in response.text


def test_import_analysis_missing_database_url_is_safe(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import job_alert_automation.config as config_module

    monkeypatch.setattr(config_module, "DEFAULT_ENV_PATH", tmp_path / ".env")
    result_path = config_module.REPO_ROOT / "output/analysis_results/api_missing_db_result.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text('{"user_id":"minjian","results":[]}', encoding="utf-8")
    client = TestClient(create_app())

    response = client.post("/api/analysis-import", json={"resultPath": str(result_path.relative_to(config_module.REPO_ROOT))})

    assert response.status_code == 503
    assert "DATABASE_URL" in response.json()["detail"]
    assert "postgres://" not in response.text
    assert "postgresql://" not in response.text
