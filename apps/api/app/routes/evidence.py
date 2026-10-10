"""Typed endpoints for deterministic evidence registration and verification."""

from fastapi import APIRouter, HTTPException

from app.evidence.models import (
    CalculationArtifact,
    CalculationKind,
    ClaimEvidence,
    ClaimRecord,
    ReplayResult,
    VerificationResult,
)
from app.evidence.replay import build_calculation_artifact, build_snapshot_reference
from app.evidence.schemas import (
    CalculationDetails,
    ClaimDetails,
    LifecycleRequest,
    LifecycleResponse,
    RegisterEvidenceRequest,
    RegisterEvidenceResponse,
    ReplayCalculationRequest,
    VerifyClaimRequest,
)
from app.evidence.verification import ClaimVerifier
from app.runtime import evidence_registry
from app.tactical.config import DEFAULT_TACTICAL_CONFIG
from app.tactical.engine import TacticalEngine
from app.tactical.schemas import AnalyzeRequest

router = APIRouter(prefix="/api/evidence", tags=["evidence"])
registry = evidence_registry
engine = TacticalEngine()


@router.post("/register", response_model=RegisterEvidenceResponse)
def register_evidence(request: RegisterEvidenceRequest) -> RegisterEvidenceResponse:
    """Register one immutable calculation artifact or claim-evidence object."""

    try:
        if request.calculation is not None:
            artifact: CalculationArtifact = registry.store_calculation(request.calculation)
            return RegisterEvidenceResponse(
                item_id=artifact.reference.calculation_id,
                item_type="CALCULATION",
            )
        claim = request.claim
        if claim is None:
            raise ValueError("claim is required")
        record: ClaimRecord = registry.store_claim(claim)
        return RegisterEvidenceResponse(item_id=record.evidence.claim_id, item_type="CLAIM")
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/calculations/{calculation_id}", response_model=CalculationDetails)
def get_calculation(calculation_id: str) -> CalculationDetails:
    """Retrieve authoritative content, hashes, versions, and dependency links."""

    try:
        artifact = registry.get_calculation(calculation_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return CalculationDetails(
        artifact=artifact,
        dependencies=registry.list_dependencies(calculation_id),
        dependents=registry.list_dependents(calculation_id),
    )


@router.post("/calculations/snapshot-analysis", response_model=CalculationDetails)
def register_snapshot_analysis(request: AnalyzeRequest) -> CalculationDetails:
    """Run and register a replayable snapshot analysis for investigation clients."""

    try:
        analysis = engine.analyze_snapshot(
            request.snapshot,
            request.ball_carrier_id,
            request.attacking_team,
        )
        artifact = build_calculation_artifact(
            CalculationKind.SNAPSHOT_ANALYSIS,
            request.model_dump(mode="python"),
            analysis,
            DEFAULT_TACTICAL_CONFIG,
            request.snapshot.snapshot_id,
            (build_snapshot_reference(request.snapshot),),
            {
                "opportunity_score": "score",
                "pressure_summary.at_ball_carrier": "modeled-pressure-index",
                "pressure_summary.mean_attacking_player_pressure": (
                    "modeled-pressure-index"
                ),
                "pressure_summary.maximum_attacking_player_pressure": (
                    "modeled-pressure-index"
                ),
            },
        )
        stored = registry.store_calculation(artifact)
        calculation_id = stored.reference.calculation_id
        return CalculationDetails(
            artifact=stored,
            dependencies=registry.list_dependencies(calculation_id),
            dependents=registry.list_dependents(calculation_id),
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/claims/{claim_id}", response_model=ClaimDetails)
def get_claim(claim_id: str) -> ClaimDetails:
    """Retrieve a stored claim, current decision, history, and dependencies."""

    try:
        record = registry.get_claim(claim_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return ClaimDetails(
        record=record,
        dependencies=registry.list_dependencies(claim_id),
        dependents=registry.list_dependents(claim_id),
    )


@router.post("/verify", response_model=VerificationResult)
def verify_claim(request: VerifyClaimRequest) -> VerificationResult:
    """Verify a registered or inline claim against deterministic evidence."""

    try:
        claim: ClaimEvidence
        if request.claim is not None:
            claim = request.claim
        else:
            claim = registry.get_claim(request.claim_id or "").evidence
        return ClaimVerifier(registry).verify(claim)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/replay", response_model=ReplayResult)
def replay_calculation(request: ReplayCalculationRequest) -> ReplayResult:
    """Replay a deterministic calculation and compare authoritative output."""

    try:
        return registry.replay(
            request.calculation_id,
            input_override=request.input_override,
            configuration_override=request.configuration_override,
        )
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/invalidate", response_model=LifecycleResponse)
def invalidate_evidence(request: LifecycleRequest) -> LifecycleResponse:
    """Invalidate evidence and all transitive dependents without deleting history."""

    try:
        return LifecycleResponse(
            affected_ids=registry.invalidate(request.evidence_id, request.reason)
        )
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/stale", response_model=LifecycleResponse)
def mark_evidence_stale(request: LifecycleRequest) -> LifecycleResponse:
    """Mark evidence and transitive dependents stale without invalidating history."""

    try:
        return LifecycleResponse(
            affected_ids=registry.mark_stale(request.evidence_id, request.reason)
        )
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
