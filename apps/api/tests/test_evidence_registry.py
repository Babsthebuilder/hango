from copy import deepcopy

import pytest

from app.evidence.config import EvidenceConfig
from app.evidence.dependency_graph import DependencyCycleError, EvidenceDependencyGraph
from app.evidence.models import (
    CalculationArtifact,
    CalculationKind,
    ClaimEvidence,
    ValidityState,
    VerificationStatus,
)
from app.evidence.registry import InMemoryEvidenceRegistry
from app.evidence.replay import (
    build_calculation_artifact,
    build_calculation_evidence_reference,
    build_counterfactual_reference,
    compare_numeric_outputs,
    replay_calculation,
)
from app.evidence.verification import ClaimVerifier
from app.models import SyntheticFixture, Team
from app.tactical.config import DEFAULT_TACTICAL_CONFIG
from app.tactical.engine import TacticalEngine


def _registry_with_chain(
    artifact: CalculationArtifact,
    claim: ClaimEvidence,
) -> InMemoryEvidenceRegistry:
    registry = InMemoryEvidenceRegistry()
    registry.store_calculation(artifact)
    registry.store_claim(claim)
    return registry


def test_registry_stores_and_retrieves_calculation_and_claim(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    registry = _registry_with_chain(evidence_artifact, supported_claim)

    assert registry.get_calculation(evidence_artifact.reference.calculation_id) == evidence_artifact
    assert registry.get_claim(supported_claim.claim_id).evidence == supported_claim
    assert registry.list_calculations() == (evidence_artifact,)
    assert len(registry.list_claims()) == 1


def test_dependency_lookup_and_transitive_dependents(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    registry = _registry_with_chain(evidence_artifact, supported_claim)
    snapshot_reference = evidence_artifact.reference.created_from[0].reference_id

    dependencies = registry.list_dependencies(supported_claim.claim_id)
    dependents = registry.list_dependents(snapshot_reference)

    assert evidence_artifact.reference.calculation_id in dependencies
    assert snapshot_reference in dependencies
    assert evidence_artifact.reference.calculation_id in dependents
    assert supported_claim.claim_id in dependents


def test_calculation_to_calculation_dependency_propagates_staleness(
    evidence_artifact: CalculationArtifact,
    positive_fixture: SyntheticFixture,
) -> None:
    interaction = TacticalEngine().compute_interaction(
        positive_fixture.snapshot,
        positive_fixture.counterfactual,
        "H10",
        "H07",
        "H08",
        Team.HOME,
    )
    interaction_artifact = build_calculation_artifact(
        CalculationKind.INTERACTION,
        {
            "snapshot": positive_fixture.snapshot.model_dump(mode="python"),
            "counterfactual": positive_fixture.counterfactual.model_dump(mode="python"),
            "ball_carrier_id": "H10",
            "support_b_id": "H07",
            "support_c_id": "H08",
            "attacking_team": Team.HOME,
        },
        interaction,
        DEFAULT_TACTICAL_CONFIG,
        positive_fixture.snapshot.snapshot_id,
        (
            evidence_artifact.reference.created_from[0],
            build_counterfactual_reference(positive_fixture.counterfactual),
            build_calculation_evidence_reference(evidence_artifact),
        ),
        {"interaction_value": "score"},
    )
    registry = InMemoryEvidenceRegistry()
    registry.store_calculation(evidence_artifact)
    registry.store_calculation(interaction_artifact)

    affected = registry.mark_stale(
        evidence_artifact.reference.calculation_id,
        "upstream analysis superseded",
    )

    assert interaction_artifact.reference.calculation_id in affected
    assert registry.get_calculation(
        interaction_artifact.reference.calculation_id
    ).reference.validity_state == ValidityState.STALE


def test_dependency_graph_rejects_cycles_and_returns_chain() -> None:
    graph = EvidenceDependencyGraph()
    graph.add_dependency("calculation", "snapshot")
    graph.add_dependency("claim", "calculation")

    assert graph.dependency_chain("claim", "snapshot") == (
        "claim",
        "calculation",
        "snapshot",
    )
    with pytest.raises(DependencyCycleError, match="cycle"):
        graph.add_dependency("snapshot", "claim")


def test_staleness_propagates_transitively_and_preserves_records(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    registry = _registry_with_chain(evidence_artifact, supported_claim)
    snapshot_reference = evidence_artifact.reference.created_from[0].reference_id

    affected = registry.mark_stale(snapshot_reference, "snapshot corrected")

    assert evidence_artifact.reference.calculation_id in affected
    assert supported_claim.claim_id in affected
    assert (
        registry.get_calculation(evidence_artifact.reference.calculation_id).reference.validity_state
        == ValidityState.STALE
    )
    assert registry.get_claim(supported_claim.claim_id).evidence.verification_status == (
        VerificationStatus.STALE
    )
    assert registry.audit_log


def test_invalidation_is_distinct_and_propagates_transitively(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    registry = _registry_with_chain(evidence_artifact, supported_claim)

    registry.invalidate(evidence_artifact.reference.calculation_id, "calculation defect")

    assert (
        registry.get_calculation(evidence_artifact.reference.calculation_id).reference.validity_state
        == ValidityState.INVALIDATED
    )
    claim = registry.get_claim(supported_claim.claim_id).evidence
    assert claim.validity_state == ValidityState.INVALIDATED
    assert claim.verification_status == VerificationStatus.REJECTED


def test_exact_replay_succeeds(evidence_artifact: CalculationArtifact) -> None:
    registry = InMemoryEvidenceRegistry()
    registry.store_calculation(evidence_artifact)

    replay = registry.replay(evidence_artifact.reference.calculation_id)

    assert replay.replay_success
    assert replay.expected_output_hash == replay.actual_output_hash
    assert replay.numeric_differences == ()


def test_changed_input_fails_replay_and_marks_calculation_stale(
    evidence_artifact: CalculationArtifact,
) -> None:
    registry = InMemoryEvidenceRegistry()
    registry.store_calculation(evidence_artifact)
    changed_input = deepcopy(evidence_artifact.input_payload)
    changed_input["snapshot"]["players"][0]["position"]["x"] += 1.0

    replay = registry.replay(
        evidence_artifact.reference.calculation_id,
        input_override=changed_input,
    )

    assert not replay.replay_success
    assert "input hash differs" in replay.explanation
    assert registry.get_calculation(
        evidence_artifact.reference.calculation_id
    ).reference.validity_state == ValidityState.STALE


def test_fixture_evidence_chain_becomes_stale_after_input_change(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    registry = _registry_with_chain(evidence_artifact, supported_claim)
    changed_input = deepcopy(evidence_artifact.input_payload)
    changed_input["snapshot"]["players"][0]["position"]["x"] += 1.0

    replay = registry.replay(
        evidence_artifact.reference.calculation_id,
        input_override=changed_input,
    )
    claim = registry.get_claim(supported_claim.claim_id).evidence
    verification = ClaimVerifier(registry).verify(claim)

    assert not replay.replay_success
    assert claim.validity_state == ValidityState.STALE
    assert verification.status == VerificationStatus.STALE


def test_changed_config_version_becomes_stale(evidence_artifact: CalculationArtifact) -> None:
    registry = InMemoryEvidenceRegistry()
    registry.store_calculation(evidence_artifact)
    changed_config = deepcopy(evidence_artifact.configuration_payload)
    changed_config["configuration_version"] = "tactical-config-v0.2"

    replay = registry.replay(
        evidence_artifact.reference.calculation_id,
        configuration_override=changed_config,
    )

    assert not replay.configuration_match
    assert registry.get_calculation(
        evidence_artifact.reference.calculation_id
    ).reference.validity_state == ValidityState.STALE


def test_changed_model_version_becomes_stale(evidence_artifact: CalculationArtifact) -> None:
    registry = InMemoryEvidenceRegistry()
    registry.store_calculation(evidence_artifact)
    changed_config = deepcopy(evidence_artifact.configuration_payload)
    changed_config["model_version"] = "tactical-v0.2"

    replay = registry.replay(
        evidence_artifact.reference.calculation_id,
        configuration_override=changed_config,
    )

    assert not replay.version_match
    assert registry.get_calculation(
        evidence_artifact.reference.calculation_id
    ).reference.validity_state == ValidityState.STALE


def test_calculation_id_collision_with_different_artifact_is_rejected(
    evidence_artifact: CalculationArtifact,
) -> None:
    registry = InMemoryEvidenceRegistry()
    registry.store_calculation(evidence_artifact)
    conflicting = evidence_artifact.model_copy(
        update={"numerical_units": {"opportunity_score": "percent"}}
    )

    with pytest.raises(ValueError, match="collision"):
        registry.store_calculation(conflicting)


def test_output_mismatch_is_detected(evidence_artifact: CalculationArtifact) -> None:
    tampered_output = deepcopy(evidence_artifact.authoritative_output)
    tampered_output["opportunity_score"] += 0.1
    tampered_artifact = evidence_artifact.model_copy(
        update={"authoritative_output": tampered_output}
    )

    replay = replay_calculation(tampered_artifact)

    assert not replay.replay_success
    assert any(not difference.within_tolerance for difference in replay.numeric_differences)


def test_numeric_comparison_uses_absolute_and_relative_tolerance() -> None:
    config = EvidenceConfig(absolute_tolerance=1e-6, relative_tolerance=1e-6)

    within, structural = compare_numeric_outputs({"value": 1.0}, {"value": 1.0000005}, config)
    outside, _ = compare_numeric_outputs({"value": 1.0}, {"value": 1.01}, config)

    assert structural
    assert within[0].within_tolerance
    assert not outside[0].within_tolerance
