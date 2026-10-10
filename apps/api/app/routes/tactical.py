"""Typed fixture and tactical-analysis HTTP routes."""

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.fixtures import load_fixture
from app.models import SyntheticFixture
from app.tactical.engine import TacticalEngine
from app.tactical.schemas import (
    AnalyzeRequest,
    CompareRequest,
    CounterfactualComparison,
    InteractionRequest,
    InteractionResult,
    PressureGridComparison,
    PressureGridRequest,
    SnapshotAnalysis,
)

router = APIRouter(prefix="/api", tags=["tactical"])
FIXTURE_DIRECTORY = Path(__file__).parents[4] / "data" / "fixtures"
engine = TacticalEngine()


@router.get("/fixtures", response_model=list[str])
def list_fixtures() -> list[str]:
    """List stable fixture IDs derived from file names."""

    return [path.stem for path in sorted(FIXTURE_DIRECTORY.glob("*.json"))]


@router.get("/fixtures/{fixture_id}", response_model=SyntheticFixture)
def get_fixture(fixture_id: str) -> SyntheticFixture:
    """Return one validated fixture."""

    path = FIXTURE_DIRECTORY / f"{fixture_id}.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="fixture not found")
    return load_fixture(path)


@router.post("/tactical/analyze", response_model=SnapshotAnalysis)
def analyze_tactical_state(request: AnalyzeRequest) -> SnapshotAnalysis:
    """Analyze one validated snapshot without external services."""

    try:
        return engine.analyze_snapshot(
            request.snapshot,
            request.ball_carrier_id,
            request.attacking_team,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/tactical/interaction", response_model=InteractionResult)
def analyze_interaction(request: InteractionRequest) -> InteractionResult:
    """Compute four-state modeled relational interaction."""

    try:
        return engine.compute_interaction(
            request.snapshot,
            request.counterfactual,
            request.ball_carrier_id,
            request.support_b_id,
            request.support_c_id,
            request.attacking_team,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/tactical/compare", response_model=CounterfactualComparison)
def compare_tactical_states(request: CompareRequest) -> CounterfactualComparison:
    """Compare baseline and explicit hypothetical state without client-side calculation."""

    try:
        return engine.compare_counterfactual(
            request.snapshot,
            request.counterfactual,
            request.ball_carrier_id,
            request.attacking_team,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/tactical/pressure-grid", response_model=PressureGridComparison)
def analyze_pressure_grid(request: PressureGridRequest) -> PressureGridComparison:
    """Return versioned baseline and optional hypothetical modeled pressure fields."""

    try:
        baseline = engine.defensive_pressure_grid(request.snapshot, request.attacking_team)
        alternative = None
        if request.counterfactual is not None:
            alternative_snapshot = engine.materialize_counterfactual(
                request.snapshot,
                request.counterfactual,
            )
            alternative = engine.defensive_pressure_grid(
                alternative_snapshot,
                request.attacking_team,
            )
        return PressureGridComparison(baseline=baseline, alternative=alternative)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
