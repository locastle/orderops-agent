"""Health and version endpoints.

`/health` is deliberately dependency free: the public demo uses it to warm up
the serverless function and to wake the database before the first real query,
so it must answer even when the database is still asleep or down.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-api"}


@router.get("/api/version")
async def version() -> dict[str, str]:
    return {"service": "ai-api", "version": "0.1.0"}
