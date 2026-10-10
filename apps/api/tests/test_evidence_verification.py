
import pytest

from app.evidence.models import (
    CalculationArtifact,
    ClaimEvidence,
    ClaimType,
    EvidenceKind,
    EvidenceReference,
    VerificationStatus,
)
from app.evidence.registry import InMemoryEvidenceRegistry
from app.evidence.verification import ClaimVerifier


def _verify(
    artifact: CalculationArtifact,
    claim: ClaimEvidence,
) -> tuple[InMemoryEvidenceRegistry, VerificationStatus]:
    registry = InMemoryEvidenceRegistry()
    registry.store_calculation(artifact)
    registry.store_claim(claim)
    result = ClaimVerifier(registry).verify(claim)
    return registry, result.status


def test_valid_numerical_model_claim_is_supported(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    registry, status = _verify(evidence_artifact, supported_claim)

    assert status == VerificationStatus.SUPPORTED
    stored = registry.get_claim(supported_claim.claim_id)
    assert stored.evidence.verification_status == VerificationStatus.SUPPORTED
    assert len(stored.verification_history) == 1


def test_numerical_assertion_within_tolerance_is_supported(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    assertion = supported_claim.numerical_assertions[0]
    claim = supported_claim.model_copy(
        update={
            "claim_id": "claim-within-tolerance",
            "numerical_assertions": (
                assertion.model_copy(update={"value": assertion.value + 5e-10}),
            ),
        }
    )

    _, status = _verify(evidence_artifact, claim)

    assert status == VerificationStatus.SUPPORTED


@pytest.mark.parametrize(
    ("assertion_update", "reason_fragment"),
    [
        ({"value_delta": 0.1}, "does not match"),
        ({"unit": "percent"}, "Unit mismatch"),
    ],
)
def test_wrong_number_or_unit_is_rejected(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
    assertion_update: dict[str, object],
    reason_fragment: str,
) -> None:
    assertion = supported_claim.numerical_assertions[0]
    updates = dict(assertion_update)
    if "value_delta" in updates:
        updates["value"] = assertion.value + float(updates.pop("value_delta"))
    changed = assertion.model_copy(update=updates)
    claim = supported_claim.model_copy(
        update={
            "claim_id": f"claim-wrong-{changed.unit}",
            "numerical_assertions": (changed,),
        }
    )
    registry = InMemoryEvidenceRegistry()
    registry.store_calculation(evidence_artifact)

    result = ClaimVerifier(registry).verify(claim)

    assert result.status == VerificationStatus.REJECTED
    assert reason_fragment in result.reason


def test_missing_calculation_is_rejected(supported_claim: ClaimEvidence) -> None:
    result = ClaimVerifier(InMemoryEvidenceRegistry()).verify(supported_claim)

    assert result.status == VerificationStatus.REJECTED
    assert "evidence does not exist" in result.reason


def test_stale_evidence_produces_stale_claim(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    registry = InMemoryEvidenceRegistry()
    registry.store_calculation(evidence_artifact)
    registry.store_claim(supported_claim)
    registry.mark_stale(evidence_artifact.reference.calculation_id, "config superseded")

    result = ClaimVerifier(registry).verify(
        registry.get_claim(supported_claim.claim_id).evidence
    )

    assert result.status == VerificationStatus.STALE


def test_invalidated_evidence_rejects_claim(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    registry = InMemoryEvidenceRegistry()
    registry.store_calculation(evidence_artifact)
    registry.store_claim(supported_claim)
    registry.invalidate(evidence_artifact.reference.calculation_id, "known defect")

    result = ClaimVerifier(registry).verify(
        registry.get_claim(supported_claim.claim_id).evidence
    )

    assert result.status == VerificationStatus.REJECTED


@pytest.mark.parametrize(
    "claim_text",
    [
        "The defender was dragged out of position.",
        "The support movement caused the lane to open.",
    ],
)
def test_unsupported_intent_or_causality_is_qualified(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
    claim_text: str,
) -> None:
    claim = supported_claim.model_copy(
        update={
            "claim_id": f"claim-qualified-{len(claim_text)}",
            "claim_text": claim_text,
            "claim_type": ClaimType.INTERPRETATION,
            "evidence_classification": ClaimType.INTERPRETATION,
        }
    )
    registry = InMemoryEvidenceRegistry()
    registry.store_calculation(evidence_artifact)

    result = ClaimVerifier(registry).verify(claim)

    assert result.status == VerificationStatus.QUALIFIED
    assert result.suggested_claim_text is not None


def test_uncalibrated_goal_probability_claim_is_rejected(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    claim = supported_claim.model_copy(
        update={
            "claim_id": "claim-false-probability",
            "claim_text": "This pass had a 34% chance of creating a goal.",
        }
    )
    registry = InMemoryEvidenceRegistry()
    registry.store_calculation(evidence_artifact)

    result = ClaimVerifier(registry).verify(claim)

    assert result.status == VerificationStatus.REJECTED
    assert "calibrated probability" in result.reason


def test_model_estimate_cannot_be_misclassified_as_observation(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    claim = supported_claim.model_copy(
        update={
            "claim_id": "claim-misclassified-observation",
            "claim_type": ClaimType.OBSERVED,
            "evidence_classification": ClaimType.OBSERVED,
        }
    )
    registry = InMemoryEvidenceRegistry()
    registry.store_calculation(evidence_artifact)

    result = ClaimVerifier(registry).verify(claim)

    assert result.status == VerificationStatus.REJECTED
    assert "observed claim" in result.reason


def test_generated_prose_cannot_verify_itself(
    supported_claim: ClaimEvidence,
) -> None:
    prose_reference = EvidenceReference(
        reference_id="prose:self:0123456789abcdef",
        evidence_kind=EvidenceKind.GENERATED_PROSE,
        object_id=supported_claim.claim_id,
        content_hash="0" * 64,
        source_provenance="generated narrative",
        schema_version=supported_claim.schema_version,
    )
    claim = supported_claim.model_copy(
        update={
            "claim_id": "claim-self-verification",
            "evidence_references": (prose_reference,),
            "calculation_references": (),
            "numerical_assertions": (),
        }
    )

    result = ClaimVerifier(InMemoryEvidenceRegistry()).verify(claim)

    assert result.status == VerificationStatus.REJECTED
    assert "Generated prose" in result.reason


def test_claim_without_deterministic_references_is_rejected(
    supported_claim: ClaimEvidence,
) -> None:
    claim = supported_claim.model_copy(
        update={
            "claim_id": "claim-no-evidence",
            "evidence_references": (),
            "calculation_references": (),
            "numerical_assertions": (),
        }
    )

    result = ClaimVerifier(InMemoryEvidenceRegistry()).verify(claim)

    assert result.status == VerificationStatus.REJECTED
    assert "cannot verify itself" in result.reason


def test_claim_cannot_register_an_invented_snapshot_as_authority(
    supported_claim: ClaimEvidence,
) -> None:
    invented = supported_claim.evidence_references[0].model_copy(
        update={"reference_id": "snapshot:invented:0123456789abcdef"}
    )
    claim = supported_claim.model_copy(
        update={
            "claim_id": "claim-invented-source",
            "claim_type": ClaimType.OBSERVED,
            "evidence_classification": ClaimType.OBSERVED,
            "evidence_references": (invented,),
            "calculation_references": (),
            "numerical_assertions": (),
        }
    )
    registry = InMemoryEvidenceRegistry()
    registry.store_claim(claim)

    result = ClaimVerifier(registry).verify(claim)

    assert result.status == VerificationStatus.REJECTED
    assert "does not exist" in result.reason


def test_numerical_assertion_must_cite_its_calculation(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    claim = supported_claim.model_copy(
        update={
            "claim_id": "claim-uncited-number",
            "calculation_references": (),
            "claim_type": ClaimType.INTERPRETATION,
            "evidence_classification": ClaimType.INTERPRETATION,
        }
    )
    registry = InMemoryEvidenceRegistry()
    registry.store_calculation(evidence_artifact)

    result = ClaimVerifier(registry).verify(claim)

    assert result.status == VerificationStatus.REJECTED
    assert "not cited" in result.reason
