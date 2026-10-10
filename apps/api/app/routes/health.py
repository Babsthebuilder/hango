"""Health route."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    """Typed health-check response."""

    status: Literal["ok"]
    service: Literal["hango-api"]


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return process health without requiring external services."""

    return HealthResponse(status="ok", service="hango-api")
