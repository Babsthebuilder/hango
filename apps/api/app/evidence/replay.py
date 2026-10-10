"""Deterministic construction and replay of tactical calculation artifacts."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from app.evidence.config import DEFAULT_EVIDENCE_CONFIG, EvidenceConfig
from app.evidence.hashing import hash_config, hash_counterfactual, hash_snapshot, stable_hash
from app.evidence.models import (
    CalculationArtifact,
    CalculationKind,
    CalculationReference,
    EvidenceKind,
    EvidenceReference,
    NumericDifference,
    ReplayResult,
)
from app.models.state import CounterfactualState, Snapshot, Team
from app.tactical.config import TacticalConfig
from app.tactical.engine import TacticalEngine


def build_snapshot_reference(
    snapshot: Snapshot,
    evidence_config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG,
) -> EvidenceReference:
    """Create a stable source reference for an immutable football snapshot."""

    content_hash = hash_snapshot(snapshot, evidence_config)
    return EvidenceReference(
        reference_id=f"snapshot:{snapshot.snapshot_id}:{content_hash[:20]}",
        evidence_kind=EvidenceKind.SNAPSHOT,
        object_id=snapshot.snapshot_id,
        content_hash=content_hash,
        snapshot_id=snapshot.snapshot_id,
        source_provenance=snapshot.provenance,
        schema_version=snapshot.schema_version,
    )


def build_counterfactual_reference(
    counterfactual: CounterfactualState,
    evidence_config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG,
) -> EvidenceReference:
    """Create a stable source reference for a hypothetical state."""

    content_hash = hash_counterfactual(counterfactual, evidence_config)
    return EvidenceReference(
        reference_id=f"counterfactual:{counterfactual.counterfactual_id}:{content_hash[:20]}",
        evidence_kind=EvidenceKind.COUNTERFACTUAL,
        object_id=counterfactual.counterfactual_id,
        content_hash=content_hash,
        snapshot_id=counterfactual.baseline_snapshot_id,
        source_provenance=counterfactual.provenance,
        schema_version=evidence_config.schema_version,
    )


def build_calculation_evidence_reference(
    artifact: CalculationArtifact,
) -> EvidenceReference:
    """Expose a stored calculation as an upstream dependency for later artifacts."""

    reference = artifact.reference
    return EvidenceReference(
        reference_id=reference.calculation_id,
        evidence_kind=EvidenceKind.TACTICAL_CALCULATION,
        object_id=reference.calculation_id,
        content_hash=reference.output_hash,
        snapshot_id=reference.snapshot_id,
        calculation_id=reference.calculation_id,
        model_version=reference.model_version,
        source_provenance=f"deterministic {reference.calculation_kind.value.lower()}",
        validity_state=reference.validity_state,
        schema_version=reference.schema_version,
    )


def build_calculation_artifact(
    calculation_kind: CalculationKind,
    input_payload: dict[str, Any],
    authoritative_output: Any,
    tactical_config: TacticalConfig,
    snapshot_id: str,
    created_from: tuple[EvidenceReference, ...],
    numerical_units: dict[str, str] | None = None,
    evidence_config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG,
) -> CalculationArtifact:
    """Build a content-addressed artifact from authoritative semantic content."""

    output_payload = _payload(authoritative_output)
    config_payload = tactical_config.model_dump(mode="python")
    input_hash = stable_hash(input_payload, evidence_config)
    output_hash = stable_hash(output_payload, evidence_config)
    identity_hash = stable_hash(
        {
            "calculation_kind": calculation_kind,
            "input_hash": input_hash,
            "output_hash": output_hash,
            "model_version": tactical_config.model_version,
            "configuration_version": tactical_config.configuration_version,
            "schema_version": evidence_config.schema_version,
        },
        evidence_config,
    )
    prefix = calculation_kind.value.lower().replace("_", "-")
    calculation_id = (
        f"calc:{prefix}:{identity_hash[: evidence_config.calculation_id_hash_length]}"
    )
    reference = CalculationReference(
        calculation_id=calculation_id,
        calculation_kind=calculation_kind,
        input_hash=input_hash,
        output_hash=output_hash,
        snapshot_id=snapshot_id,
        model_version=tactical_config.model_version,
        configuration_version=tactical_config.configuration_version,
        schema_version=evidence_config.schema_version,
        created_from=created_from,
    )
    return CalculationArtifact(
        reference=reference,
        input_payload=input_payload,
        authoritative_output=output_payload,
        configuration_payload=config_payload,
        numerical_units=numerical_units or {},
    )


def replay_calculation(
    artifact: CalculationArtifact,
    *,
    input_override: dict[str, Any] | None = None,
    configuration_override: dict[str, Any] | None = None,
    stale_dependencies: tuple[str, ...] = (),
    evidence_config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG,
) -> ReplayResult:
    """Re-run one calculation and compare it with its authoritative result."""

    inputs = input_override if input_override is not None else artifact.input_payload
    config_payload = (
        configuration_override
        if configuration_override is not None
        else artifact.configuration_payload
    )
    tactical_config = TacticalConfig.model_validate(config_payload)
    input_match = stable_hash(inputs, evidence_config) == artifact.reference.input_hash
    version_match = tactical_config.model_version == artifact.reference.model_version
    configuration_match = (
        tactical_config.configuration_version == artifact.reference.configuration_version
        and hash_config(config_payload, evidence_config)
        == hash_config(artifact.configuration_payload, evidence_config)
    )

    try:
        actual_output = _execute(artifact.reference.calculation_kind, inputs, tactical_config)
    except (KeyError, TypeError, ValueError) as error:
        return ReplayResult(
            calculation_id=artifact.reference.calculation_id,
            replay_success=False,
            expected_output_hash=artifact.reference.output_hash,
            actual_output_hash=None,
            version_match=version_match,
            configuration_match=configuration_match,
            stale_dependencies=stale_dependencies,
            explanation=f"Replay input could not be executed: {error}",
        )

    actual_payload = _payload(actual_output)
    actual_hash = stable_hash(actual_payload, evidence_config)
    differences, structural_match = compare_numeric_outputs(
        artifact.authoritative_output,
        actual_payload,
        evidence_config,
    )
    numeric_match = all(difference.within_tolerance for difference in differences)
    replay_success = (
        input_match
        and version_match
        and configuration_match
        and not stale_dependencies
        and structural_match
        and numeric_match
    )
    reasons: list[str] = []
    if not input_match:
        reasons.append("input hash differs from the authoritative input")
    if not version_match:
        reasons.append("model version differs")
    if not configuration_match:
        reasons.append("configuration differs")
    if stale_dependencies:
        reasons.append("one or more dependencies are not valid")
    if not structural_match:
        reasons.append("non-numeric output structure differs")
    if not numeric_match:
        reasons.append("numeric output differs beyond tolerance")
    if not reasons and actual_hash != artifact.reference.output_hash:
        reasons.append("output hash differs only within configured numeric tolerance")
    explanation = "Replay matched authoritative evidence" if not reasons else "; ".join(reasons)
    return ReplayResult(
        calculation_id=artifact.reference.calculation_id,
        replay_success=replay_success,
        expected_output_hash=artifact.reference.output_hash,
        actual_output_hash=actual_hash,
        numeric_differences=differences,
        version_match=version_match,
        configuration_match=configuration_match,
        stale_dependencies=stale_dependencies,
        explanation=explanation,
    )


def compare_numeric_outputs(
    expected: Any,
    actual: Any,
    config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG,
) -> tuple[tuple[NumericDifference, ...], bool]:
    """Compare nested outputs, using tolerances for numeric leaves."""

    differences: list[NumericDifference] = []
    structural_match = _compare_value(expected, actual, "$", differences, config)
    return tuple(differences), structural_match


def _compare_value(
    expected: Any,
    actual: Any,
    path: str,
    differences: list[NumericDifference],
    config: EvidenceConfig,
) -> bool:
    if _is_number(expected) and _is_number(actual):
        expected_float = float(expected)
        actual_float = float(actual)
        if expected_float != actual_float:
            differences.append(
                NumericDifference(
                    field_path=path,
                    expected=expected_float,
                    actual=actual_float,
                    absolute_difference=abs(expected_float - actual_float),
                    within_tolerance=math.isclose(
                        actual_float,
                        expected_float,
                        rel_tol=config.relative_tolerance,
                        abs_tol=config.absolute_tolerance,
                    ),
                )
            )
        return True
    if isinstance(expected, Mapping) and isinstance(actual, Mapping):
        if set(expected) != set(actual):
            return False
        return all(
            _compare_value(expected[key], actual[key], f"{path}.{key}", differences, config)
            for key in sorted(expected)
        )
    if _is_sequence(expected) and _is_sequence(actual):
        if len(expected) != len(actual):
            return False
        return all(
            _compare_value(left, right, f"{path}[{index}]", differences, config)
            for index, (left, right) in enumerate(zip(expected, actual, strict=True))
        )
    return expected == actual


def _execute(
    calculation_kind: CalculationKind,
    payload: dict[str, Any],
    config: TacticalConfig,
) -> Any:
    engine = TacticalEngine(config)
    snapshot = Snapshot.model_validate(payload["snapshot"])
    attacking_team = Team(payload["attacking_team"])
    if calculation_kind == CalculationKind.SNAPSHOT_ANALYSIS:
        return engine.analyze_snapshot(snapshot, payload["ball_carrier_id"], attacking_team)
    if calculation_kind == CalculationKind.TRIANGLE_ANALYSIS:
        return engine.analyze_triangle(
            snapshot,
            payload["ball_carrier_id"],
            payload["support_b_id"],
            payload["support_c_id"],
            attacking_team,
        )
    if calculation_kind == CalculationKind.INTERACTION:
        return engine.compute_interaction(
            snapshot,
            CounterfactualState.model_validate(payload["counterfactual"]),
            payload["ball_carrier_id"],
            payload["support_b_id"],
            payload["support_c_id"],
            attacking_team,
        )
    raise ValueError(f"unsupported calculation kind: {calculation_kind}")


def _payload(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        result = value.model_dump(mode="python")
    else:
        result = value
    if not isinstance(result, dict):
        raise TypeError("calculation output must serialize to an object")
    return result


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
