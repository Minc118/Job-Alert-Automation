from __future__ import annotations

from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import analysis, documents, gmail, jobs, me, overview, runs, users
from job_alert_automation.config import get_env_value


DEFAULT_API_CORS_ALLOWED_ORIGINS = "http://127.0.0.1:5173,http://localhost:5173"


def get_api_cors_allowed_origins() -> list[str]:
    raw_origins = get_env_value("API_CORS_ALLOWED_ORIGINS", default=DEFAULT_API_CORS_ALLOWED_ORIGINS)
    origins: list[str] = []
    for value in raw_origins.split(","):
        candidate = value.strip().rstrip("/")
        parsed = urlparse(candidate)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.path
            or parsed.params
            or parsed.query
            or parsed.fragment
        ):
            raise RuntimeError(
                "API_CORS_ALLOWED_ORIGINS must contain comma-separated http(s) origins without paths."
            )
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in origins:
            origins.append(origin)

    if not origins:
        raise RuntimeError("API_CORS_ALLOWED_ORIGINS must contain at least one frontend origin.")
    return origins


def create_app() -> FastAPI:
    app = FastAPI(
        title="Job Alert Automation Local API",
        version="0.1.0",
        description="Local read-only API for the dashboard. The browser never connects directly to Neon.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_api_cors_allowed_origins(),
        allow_credentials=False,
        allow_methods=["DELETE", "GET", "PATCH", "POST"],
        allow_headers=["Accept", "Authorization", "Content-Type"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(users.router)
    app.include_router(me.router)
    app.include_router(documents.router)
    app.include_router(gmail.router)
    app.include_router(overview.router)
    app.include_router(jobs.router)
    app.include_router(runs.router)
    app.include_router(analysis.router)
    return app


app = create_app()
