"""FastAPI entrypoint for the AI service."""

from fastapi import FastAPI

from app.api.health import router as health_router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="orderops ai-api",
        version="0.1.0",
        description="Order anomaly diagnosis agent: orchestration, knowledge base, evaluation.",
    )
    app.include_router(health_router)
    app.state.settings = settings
    return app


app = create_app()


def run() -> None:  # pragma: no cover - convenience entrypoint
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
