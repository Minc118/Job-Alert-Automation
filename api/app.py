from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import analysis, jobs, overview, runs, users


def create_app() -> FastAPI:
    app = FastAPI(
        title="Job Alert Automation Local API",
        version="0.1.0",
        description="Local read-only API for the dashboard. The browser never connects directly to Neon.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["GET", "PATCH", "POST"],
        allow_headers=["Accept", "Content-Type"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(users.router)
    app.include_router(overview.router)
    app.include_router(jobs.router)
    app.include_router(runs.router)
    app.include_router(analysis.router)
    return app


app = create_app()
