"""FastAPI application entry point."""

from fastapi import FastAPI

from app.routes.health import router as health_router
from app.routes.tactical import router as tactical_router

app = FastAPI(
    title="HANGO API",
    version="0.2.0",
    description="Deterministic football geometry, opportunity, and interaction engine.",
)
app.include_router(health_router)
app.include_router(tactical_router)
