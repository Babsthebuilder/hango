"""Typed endpoints for grounded explanation and editorial verification."""

from fastapi import APIRouter, HTTPException

from app.explanations.models import ExplanationRequest
from app.explanations.providers import LocalTemplateProvider
from app.explanations.schemas import ExplanationDetails, ExplanationLifecycleRequest
from app.explanations.service import ExplanationService
from app.runtime import evidence_registry, explanation_registry

router = APIRouter(prefix="/api/explanations", tags=["explanations"])
service = ExplanationService(
    evidence_registry,
    explanation_registry,
    (LocalTemplateProvider(),),
)


@router.post("/generate", response_model=ExplanationDetails)
def generate_explanation(request: ExplanationRequest) -> ExplanationDetails:
    """Generate locally grounded prose and run the deterministic editorial gate."""

    try:
        return ExplanationDetails(artifact=service.generate(request))
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.get("/{explanation_id}", response_model=ExplanationDetails)
def get_explanation(explanation_id: str) -> ExplanationDetails:
    """Retrieve an explanation after refreshing its upstream evidence status."""

    try:
        return ExplanationDetails(artifact=service.get(explanation_id))
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{explanation_id}/verify", response_model=ExplanationDetails)
def verify_explanation(explanation_id: str) -> ExplanationDetails:
    """Re-run the deterministic editorial verifier."""

    try:
        return ExplanationDetails(artifact=service.verify(explanation_id))
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/{explanation_id}/invalidate", response_model=ExplanationDetails)
def invalidate_explanation(
    explanation_id: str,
    request: ExplanationLifecycleRequest,
) -> ExplanationDetails:
    """Invalidate generated prose without deleting editorial history."""

    try:
        return ExplanationDetails(
            artifact=service.invalidate(explanation_id, request.reason)
        )
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
