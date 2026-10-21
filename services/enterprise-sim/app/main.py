"""FastAPI entrypoint for the simulated enterprise systems.

This service plays the role of the company's internal systems: OMS, payment
gateway, inventory, warehouse (WMS), logistics and the log platform. The
agent never touches a database directly - it calls these read-only endpoints
through the tool layer, which keeps the trust boundary (and the rate limits)
in one place.

Planned read-only endpoints (Week 1 Day 3):

    GET /api/orders/{order_no}
    GET /api/orders/{order_no}/events
    GET /api/orders/{order_no}/payments
    GET /api/orders/{order_no}/inventory-locks
    GET /api/orders/{order_no}/warehouse-tasks
    GET /api/orders/{order_no}/logistics
    GET /api/logs?order_no=...&service=...&level=...

Every endpoint is GET only. There is deliberately no write path.
"""

from fastapi import FastAPI

app = FastAPI(
    title="orderops enterprise-sim",
    version="0.1.0",
    description="Read-only simulation of the order fulfilment backend systems.",
)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "enterprise-sim"}


@app.get("/api/version", tags=["health"])
async def version() -> dict[str, str]:
    return {"service": "enterprise-sim", "version": "0.1.0"}


def run() -> None:  # pragma: no cover - convenience entrypoint
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
