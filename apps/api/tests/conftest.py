from pathlib import Path

import pytest

from app.evidence.config import DEFAULT_EVIDENCE_CONFIG
from app.evidence.models import (
    CalculationArtifact,
    CalculationKind,
    ClaimEvidence,
    ClaimType,
    NumericalAssertion,
)
from app.evidence.replay import build_calculation_artifact, build_snapshot_reference
from app.fixtures import load_fixture
from app.models import SyntheticFixture, Team
from app.tactical.config import DEFAULT_TACTICAL_CONFIG
from app.tactical.engine import TacticalEngine

FIXTURE_DIRECTORY = Path(__file__).parents[3] / "data" / "fixtures"


@pytest.fixture
def positive_fixture() -> SyntheticFixture:
    return load_fixture(FIXTURE_DIRECTORY / "positive-interaction.json")


@pytest.fixture
def blocked_fixture() -> SyntheticFixture:
    return load_fixture(FIXTURE_DIRECTORY / "blocked-triangle.json")


@pytest.fixture
def neutral_fixture() -> SyntheticFixture:
    return load_fixture(FIXTURE_DIRECTORY / "neutral-interaction.json")


@pytest.fixture
def evidence_artifact(positive_fixture: SyntheticFixture) -> CalculationArtifact:
    snapshot = positive_fixture.snapshot
    result = TacticalEngine().analyze_snapshot(snapshot, "H10", Team.HOME)
    return build_calculation_artifact(
        CalculationKind.SNAPSHOT_ANALYSIS,
        {
            "snapshot": snapshot.model_dump(mode="python"),
            "ball_carrier_id": "H10",
            "attacking_team": Team.HOME,
        },
        result,
        DEFAULT_TACTICAL_CONFIG,
        snapshot.snapshot_id,
        (build_snapshot_reference(snapshot),),
        {"opportunity_score": "score"},
    )


@pytest.fixture
def supported_claim(evidence_artifact: CalculationArtifact) -> ClaimEvidence:
    score = float(evidence_artifact.authoritative_output["opportunity_score"])
    return ClaimEvidence(
        claim_id="claim-positive-opportunity",
        claim_text=f"The modeled opportunity value was {score:.9f}.",
        claim_type=ClaimType.MODEL_ESTIMATE,
        evidence_classification=ClaimType.MODEL_ESTIMATE,
        evidence_references=evidence_artifact.reference.created_from,
        numerical_assertions=(
            NumericalAssertion(
                calculation_id=evidence_artifact.reference.calculation_id,
                field_path="opportunity_score",
                value=score,
                unit="score",
            ),
        ),
        calculation_references=(evidence_artifact.reference,),
        model_version=evidence_artifact.reference.model_version,
        created_from=(evidence_artifact.reference.calculation_id,),
        schema_version=DEFAULT_EVIDENCE_CONFIG.schema_version,
    )
