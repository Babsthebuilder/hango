"""Deterministic claim-verification rules for HANGO publication safety."""

from __future__ import annotations

import math
import re
from typing import Any

from app.evidence.config import DEFAULT_EVIDENCE_CONFIG, EvidenceConfig
from app.evidence.models import (
    ClaimEvidence,
    ClaimType,
    EvidenceKind,
    ReplayResult,
    ValidityState,
    VerificationResult,
    VerificationStatus,
)
from app.evidence.registry import InMemoryEvidenceRegistry

_PROBABILITY_OVERREACH = re.compile(
    r"(?:\bprobability\b|\bgoal chance\b|\bchance of (?:a )?goal\b|\d+(?:\.\d+)?\s*%)",
    re.IGNORECASE,
)
_INTENT_OR_CAUSAL = re.compile(
    r"(?:\bdragged\b|\bintended\b|\bwanted\b|\bdeliberately\b|\bcaused\b|"
    r"\btherefore\b|\bled to\b|\bresulted in\b|\bbecause\b|\bforced\b)",
    re.IGNORECASE,
)


class ClaimVerifier:
    """Verify claims only from registered deterministic evidence."""

    def __init__(
        self,
        registry: InMemoryEvidenceRegistry,
        config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG,
    ) -> None:
        self.registry = registry
        self.config = config

    def verify(self, claim: ClaimEvidence) -> VerificationResult:
        """Return exactly one publication status and preserve the decision."""

        result = self._verify(claim)
        try:
            self.registry.get_claim(claim.claim_id)
        except KeyError:
            pass
        else:
            self.registry.record_verification(result)
        return result

    def _verify(self, claim: ClaimEvidence) -> VerificationResult:
        checked_ids: list[str] = []
        replay_results: list[ReplayResult] = []

        if claim.schema_version != self.config.schema_version:
            return self._result(
                claim,
                VerificationStatus.STALE,
                "Claim evidence schema version requires revalidation",
            )
        if claim.validity_state == ValidityState.INVALIDATED:
            return self._result(claim, VerificationStatus.REJECTED, "Claim evidence is invalidated")
        if claim.validity_state == ValidityState.STALE:
            return self._result(claim, VerificationStatus.STALE, "Claim evidence is stale")
        if claim.claim_type != claim.evidence_classification:
            return self._result(
                claim,
                VerificationStatus.REJECTED,
                "Claim type does not match its evidence classification",
            )
        if not claim.evidence_references and not claim.calculation_references:
            return self._result(
                claim,
                VerificationStatus.REJECTED,
                "Generated or unsupported prose cannot verify itself",
            )
        if claim.claim_id in claim.created_from:
            return self._result(
                claim,
                VerificationStatus.REJECTED,
                "A claim cannot cite itself as authoritative evidence",
            )
        non_authoritative_kinds = {
            EvidenceKind.CLAIM_EVIDENCE,
            EvidenceKind.CLAIM_RECORD,
            EvidenceKind.GENERATED_PROSE,
        }
        if any(
            reference.evidence_kind in non_authoritative_kinds
            for reference in claim.evidence_references
        ):
            return self._result(
                claim,
                VerificationStatus.REJECTED,
                "Generated prose and claims are not authoritative source evidence",
            )
        if claim.claim_type == ClaimType.OBSERVED and claim.calculation_references:
            return self._result(
                claim,
                VerificationStatus.REJECTED,
                "An observed claim cannot be supported by calculated output",
            )
        if claim.claim_type == ClaimType.OBSERVED and any(
            reference.evidence_kind != EvidenceKind.SNAPSHOT
            for reference in claim.evidence_references
        ):
            return self._result(
                claim,
                VerificationStatus.REJECTED,
                "Observed claims require observed snapshot evidence",
            )
        if claim.claim_type in {ClaimType.CALCULATED, ClaimType.MODEL_ESTIMATE} and not (
            claim.calculation_references
        ):
            return self._result(
                claim,
                VerificationStatus.REJECTED,
                "Calculated and model-estimate claims require a calculation reference",
            )

        for reference in claim.evidence_references:
            checked_ids.append(reference.reference_id)
            try:
                stored = self.registry.get_evidence(reference.reference_id)
            except KeyError:
                return self._result(
                    claim,
                    VerificationStatus.REJECTED,
                    f"Referenced evidence does not exist: {reference.reference_id}",
                    checked_ids=checked_ids,
                )
            if stored.content_hash != reference.content_hash:
                return self._result(
                    claim,
                    VerificationStatus.REJECTED,
                    f"Evidence hash mismatch: {reference.reference_id}",
                    checked_ids=checked_ids,
                )
            if (
                stored.evidence_kind == EvidenceKind.SNAPSHOT
                and stored.schema_version not in self.config.compatible_snapshot_schema_versions
            ):
                return self._result(
                    claim,
                    VerificationStatus.STALE,
                    f"Snapshot schema is not compatible: {stored.schema_version}",
                    checked_ids=checked_ids,
                )
            lifecycle = self._lifecycle_result(claim, stored.validity_state, reference.reference_id)
            if lifecycle is not None:
                return lifecycle

        for reference in claim.calculation_references:
            checked_ids.append(reference.calculation_id)
            try:
                artifact = self.registry.get_calculation(reference.calculation_id)
            except KeyError:
                return self._result(
                    claim,
                    VerificationStatus.REJECTED,
                    f"Referenced calculation does not exist: {reference.calculation_id}",
                    checked_ids=checked_ids,
                )
            stored = artifact.reference
            if stored.schema_version != self.config.schema_version:
                return self._result(
                    claim,
                    VerificationStatus.STALE,
                    f"Calculation schema requires revalidation: {reference.calculation_id}",
                    checked_ids=checked_ids,
                )
            if (
                stored.input_hash != reference.input_hash
                or stored.output_hash != reference.output_hash
                or stored.model_version != claim.model_version
                or stored.configuration_version != reference.configuration_version
                or stored.schema_version != reference.schema_version
            ):
                return self._result(
                    claim,
                    VerificationStatus.REJECTED,
                    f"Calculation identity or version mismatch: {reference.calculation_id}",
                    checked_ids=checked_ids,
                )
            lifecycle = self._lifecycle_result(
                claim,
                stored.validity_state,
                reference.calculation_id,
            )
            if lifecycle is not None:
                return lifecycle
            replay = self.registry.replay(reference.calculation_id)
            replay_results.append(replay)
            if not replay.replay_success:
                status = (
                    VerificationStatus.STALE
                    if not replay.version_match
                    or not replay.configuration_match
                    or replay.stale_dependencies
                    else VerificationStatus.REJECTED
                )
                return self._result(
                    claim,
                    status,
                    f"Calculation replay failed: {replay.explanation}",
                    replay_results,
                    checked_ids,
                )

        assertion_error = self._verify_numerical_assertions(claim)
        if assertion_error is not None:
            return self._result(
                claim,
                VerificationStatus.REJECTED,
                assertion_error,
                replay_results,
                checked_ids,
            )
        if _PROBABILITY_OVERREACH.search(claim.claim_text):
            return self._result(
                claim,
                VerificationStatus.REJECTED,
                "No calibrated probability model supports the probability wording",
                replay_results,
                checked_ids,
            )
        if _INTENT_OR_CAUSAL.search(claim.claim_text):
            return self._result(
                claim,
                VerificationStatus.QUALIFIED,
                "The deterministic evidence supports association, not player intent or causality",
                replay_results,
                checked_ids,
                "The positional change was associated with the calculated tactical difference.",
            )
        if claim.claim_type == ClaimType.INTERPRETATION:
            return self._result(
                claim,
                VerificationStatus.QUALIFIED,
                "Interpretive wording must remain explicitly qualified",
                replay_results,
                checked_ids,
            )
        return self._result(
            claim,
            VerificationStatus.SUPPORTED,
            "Current deterministic evidence supports the claim",
            replay_results,
            checked_ids,
        )

    def _verify_numerical_assertions(self, claim: ClaimEvidence) -> str | None:
        referenced_calculation_ids = {
            reference.calculation_id for reference in claim.calculation_references
        }
        for assertion in claim.numerical_assertions:
            if assertion.calculation_id not in referenced_calculation_ids:
                return (
                    "Numerical assertion calculation is not cited by the claim: "
                    f"{assertion.calculation_id}"
                )
            try:
                artifact = self.registry.get_calculation(assertion.calculation_id)
            except KeyError:
                return f"Numerical assertion calculation is missing: {assertion.calculation_id}"
            expected_unit = artifact.numerical_units.get(assertion.field_path)
            if expected_unit != assertion.unit:
                return (
                    f"Unit mismatch for {assertion.field_path}: "
                    f"expected {expected_unit!r}, received {assertion.unit!r}"
                )
            try:
                authoritative_value = _resolve_path(
                    artifact.authoritative_output,
                    assertion.field_path,
                )
            except (KeyError, IndexError, TypeError, ValueError):
                return f"Numerical assertion path does not exist: {assertion.field_path}"
            if not isinstance(authoritative_value, (int, float)) or isinstance(
                authoritative_value, bool
            ):
                return f"Numerical assertion path is not numeric: {assertion.field_path}"
            if not math.isclose(
                float(authoritative_value),
                assertion.value,
                rel_tol=self.config.relative_tolerance,
                abs_tol=self.config.absolute_tolerance,
            ):
                return f"Numerical assertion does not match evidence: {assertion.field_path}"
        return None

    def _lifecycle_result(
        self,
        claim: ClaimEvidence,
        state: ValidityState,
        item_id: str,
    ) -> VerificationResult | None:
        if state == ValidityState.INVALIDATED:
            return self._result(
                claim,
                VerificationStatus.REJECTED,
                f"Referenced evidence is invalidated: {item_id}",
            )
        if state == ValidityState.STALE:
            return self._result(
                claim,
                VerificationStatus.STALE,
                f"Referenced evidence is stale: {item_id}",
            )
        return None

    @staticmethod
    def _result(
        claim: ClaimEvidence,
        status: VerificationStatus,
        reason: str,
        replay_results: list[ReplayResult] | None = None,
        checked_ids: list[str] | None = None,
        suggested_claim_text: str | None = None,
    ) -> VerificationResult:
        return VerificationResult(
            claim_id=claim.claim_id,
            status=status,
            reason=reason,
            replay_results=tuple(replay_results or ()),
            checked_evidence_ids=tuple(checked_ids or ()),
            suggested_claim_text=suggested_claim_text,
        )


def _resolve_path(payload: dict[str, Any], field_path: str) -> Any:
    """Resolve a dotted path with optional numeric list segments."""

    current: Any = payload
    for segment in field_path.split("."):
        if isinstance(current, dict):
            current = current[segment]
        elif isinstance(current, (list, tuple)):
            current = current[int(segment)]
        else:
            raise TypeError(f"cannot traverse {segment}")
    return current
