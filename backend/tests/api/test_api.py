from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from api.app import create_app
from api.schemas import AnalysisImportResponse, AnalysisRequestResponse, UserJobStatusResponse


def test_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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

    def fake_set_job_status(user_id: str, job_id: int, status: str) -> UserJobStatusResponse:
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
