"""FastAPI application entry point."""

from fastapi import FastAPI

from app.routes.evidence import router as evidence_router
from app.routes.explanations import router as explanations_router
from app.routes.health import router as health_router
from app.routes.tactical import router as tactical_router

app = FastAPI(
    title="HANGO API",
    version="0.4.0",
    description=(
        "Deterministic football tactics with traceable evidence and grounded explanation."
    ),
)
app.include_router(health_router)
app.include_router(tactical_router)
app.include_router(evidence_router)
app.include_router(explanations_router)
