"""Replaceable repository interface and in-memory evidence implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.evidence.config import DEFAULT_EVIDENCE_CONFIG, EvidenceConfig
from app.evidence.dependency_graph import EvidenceDependencyGraph
from app.evidence.hashing import (
    hash_claim_evidence,
    hash_counterfactual,
    hash_snapshot,
    stable_hash,
)
from app.evidence.models import (
    CalculationArtifact,
    ClaimEvidence,
    ClaimRecord,
    EvidenceKind,
    EvidenceReference,
    ReplayResult,
    ValidityState,
    ValidityTransition,
    VerificationResult,
    VerificationStatus,
)
from app.evidence.replay import build_calculation_evidence_reference, replay_calculation


class EvidenceRegistry(ABC):
    """Persistence boundary for evidence and claim records."""

    @abstractmethod
    def store_calculation(self, artifact: CalculationArtifact) -> CalculationArtifact: ...

    @abstractmethod
    def get_calculation(self, calculation_id: str) -> CalculationArtifact: ...

    @abstractmethod
    def list_calculations(self) -> tuple[CalculationArtifact, ...]: ...

    @abstractmethod
    def store_claim(self, claim: ClaimEvidence) -> ClaimRecord: ...

    @abstractmethod
    def get_claim(self, claim_id: str) -> ClaimRecord: ...

    @abstractmethod
    def list_claims(self) -> tuple[ClaimRecord, ...]: ...

    @abstractmethod
    def list_dependencies(self, item_id: str) -> tuple[str, ...]: ...

    @abstractmethod
    def list_dependents(self, item_id: str) -> tuple[str, ...]: ...

    @abstractmethod
    def mark_stale(self, item_id: str, reason: str) -> tuple[str, ...]: ...

    @abstractmethod
    def invalidate(self, item_id: str, reason: str) -> tuple[str, ...]: ...

    @abstractmethod
    def replay(self, calculation_id: str, **kwargs: Any) -> ReplayResult: ...

    @abstractmethod
    def compare_replay(self, calculation_id: str, **kwargs: Any) -> ReplayResult: ...

    @abstractmethod
    def propagate_staleness(self, item_id: str, reason: str) -> tuple[str, ...]: ...


class InMemoryEvidenceRegistry(EvidenceRegistry):
    """Deterministic, audit-preserving in-memory registry."""

    def __init__(self, config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG) -> None:
        self.config = config
        self.graph = EvidenceDependencyGraph()
        self._calculations: dict[str, CalculationArtifact] = {}
        self._claims: dict[str, ClaimRecord] = {}
        self._evidence: dict[str, EvidenceReference] = {}
        self._claim_reference_ids: dict[str, str] = {}
        self._audit_log: list[ValidityTransition] = []

    def store_calculation(self, artifact: CalculationArtifact) -> CalculationArtifact:
        self._validate_artifact(artifact)
        calculation_id = artifact.reference.calculation_id
        existing = self._calculations.get(calculation_id)
        if existing is not None and existing != artifact:
            raise ValueError("calculation ID collision with different semantic content")
        self._calculations[calculation_id] = artifact
        self.graph.add_node(calculation_id)
        self._store_evidence(build_calculation_evidence_reference(artifact))
        for source in artifact.reference.created_from:
            self._store_evidence(source)
            self.graph.add_dependency(calculation_id, source.reference_id)
        return artifact

    def get_calculation(self, calculation_id: str) -> CalculationArtifact:
        try:
            return self._calculations[calculation_id]
        except KeyError as error:
            raise KeyError(f"calculation not found: {calculation_id}") from error

    def list_calculations(self) -> tuple[CalculationArtifact, ...]:
        return tuple(self._calculations[key] for key in sorted(self._calculations))

    def store_claim(self, claim: ClaimEvidence) -> ClaimRecord:
        claim_hash = hash_claim_evidence(claim, self.config)
        reference_id = f"claim-evidence:{claim.claim_id}:{claim_hash[:20]}"
        record_id = f"claim-record:{claim.claim_id}:{claim_hash[:20]}"
        existing = self._claims.get(claim.claim_id)
        if existing is not None and existing.evidence != claim:
            raise ValueError("claim ID already exists with different semantic content")
        record = existing or ClaimRecord(record_id=record_id, evidence=claim)
        self._claims[claim.claim_id] = record
        claim_reference = EvidenceReference(
            reference_id=reference_id,
            evidence_kind="CLAIM_EVIDENCE",
            object_id=claim.claim_id,
            content_hash=claim_hash,
            snapshot_id=_claim_snapshot_id(claim),
            model_version=claim.model_version,
            source_provenance="registered deterministic claim evidence",
            validity_state=claim.validity_state,
            schema_version=claim.schema_version,
        )
        self._store_evidence(claim_reference)
        self._claim_reference_ids[reference_id] = claim.claim_id
        self.graph.add_node(claim.claim_id)
        self.graph.add_dependency(claim.claim_id, reference_id, "HAS_EVIDENCE")
        for reference in claim.evidence_references:
            self.graph.add_node(reference.reference_id)
            self.graph.add_dependency(reference_id, reference.reference_id)
        for reference in claim.calculation_references:
            self.graph.add_dependency(reference_id, reference.calculation_id)
        for source_id in claim.created_from:
            self.graph.add_dependency(reference_id, source_id)
        return record

    def get_claim(self, claim_id: str) -> ClaimRecord:
        try:
            return self._claims[claim_id]
        except KeyError as error:
            raise KeyError(f"claim not found: {claim_id}") from error

    def list_claims(self) -> tuple[ClaimRecord, ...]:
        return tuple(self._claims[key] for key in sorted(self._claims))

    def get_evidence(self, reference_id: str) -> EvidenceReference:
        try:
            return self._evidence[reference_id]
        except KeyError as error:
            raise KeyError(f"evidence not found: {reference_id}") from error

    def list_dependencies(self, item_id: str) -> tuple[str, ...]:
        return self.graph.list_dependencies(item_id, transitive=True)

    def list_dependents(self, item_id: str) -> tuple[str, ...]:
        return self.graph.list_dependents(item_id, transitive=True)

    def mark_stale(self, item_id: str, reason: str) -> tuple[str, ...]:
        return self._propagate(item_id, ValidityState.STALE, reason)

    def invalidate(self, item_id: str, reason: str) -> tuple[str, ...]:
        return self._propagate(item_id, ValidityState.INVALIDATED, reason)

    def propagate_staleness(self, item_id: str, reason: str) -> tuple[str, ...]:
        return self.mark_stale(item_id, reason)

    def replay(
        self,
        calculation_id: str,
        **kwargs: Any,
    ) -> ReplayResult:
        artifact = self.get_calculation(calculation_id)
        stale_dependencies = tuple(
            dependency_id
            for dependency_id in self.list_dependencies(calculation_id)
            if self._validity_of(dependency_id) != ValidityState.VALID
        )
        result = replay_calculation(
            artifact,
            stale_dependencies=stale_dependencies,
            evidence_config=self.config,
            **kwargs,
        )
        if not result.replay_success:
            version_or_input_change = (
                not result.version_match
                or not result.configuration_match
                or kwargs.get("input_override") is not None
                or kwargs.get("configuration_override") is not None
                or stale_dependencies
            )
            if version_or_input_change:
                self.mark_stale(calculation_id, result.explanation)
            elif result.actual_output_hash is not None:
                self.invalidate(calculation_id, result.explanation)
        return result

    def compare_replay(self, calculation_id: str, **kwargs: Any) -> ReplayResult:
        return self.replay(calculation_id, **kwargs)

    def record_verification(self, result: VerificationResult) -> ClaimRecord:
        record = self.get_claim(result.claim_id)
        validity = record.evidence.validity_state
        if result.status == VerificationStatus.STALE:
            validity = ValidityState.STALE
        updated_evidence = record.evidence.model_copy(
            update={
                "verification_status": result.status,
                "verification_reason": result.reason,
                "validity_state": validity,
            }
        )
        updated = record.model_copy(
            update={
                "evidence": updated_evidence,
                "verification_history": (*record.verification_history, result),
            }
        )
        self._claims[result.claim_id] = updated
        return updated

    @property
    def audit_log(self) -> tuple[ValidityTransition, ...]:
        return tuple(self._audit_log)

    def clear(self) -> None:
        """Reset volatile storage; intended for isolated application tests."""

        self.__init__(self.config)

    def _store_evidence(self, reference: EvidenceReference) -> None:
        existing = self._evidence.get(reference.reference_id)
        if existing is not None and existing != reference:
            raise ValueError("evidence reference collision with different content")
        self._evidence[reference.reference_id] = reference
        self.graph.add_node(reference.reference_id)

    def _validate_artifact(self, artifact: CalculationArtifact) -> None:
        reference = artifact.reference
        if stable_hash(artifact.input_payload, self.config) != reference.input_hash:
            raise ValueError("calculation input hash does not match artifact payload")
        if stable_hash(artifact.authoritative_output, self.config) != reference.output_hash:
            raise ValueError("calculation output hash does not match artifact payload")
        if artifact.configuration_payload.get("model_version") != reference.model_version:
            raise ValueError("artifact model version does not match its reference")
        if (
            artifact.configuration_payload.get("configuration_version")
            != reference.configuration_version
        ):
            raise ValueError("artifact configuration version does not match its reference")
        snapshot_sources = tuple(
            source
            for source in reference.created_from
            if source.evidence_kind == EvidenceKind.SNAPSHOT
        )
        if len(snapshot_sources) != 1:
            raise ValueError("calculation must reference exactly one authoritative snapshot")
        snapshot_payload = artifact.input_payload.get("snapshot")
        if not isinstance(snapshot_payload, dict):
            raise ValueError("calculation input must contain a snapshot object")
        snapshot_source = snapshot_sources[0]
        if hash_snapshot(snapshot_payload, self.config) != snapshot_source.content_hash:
            raise ValueError("snapshot source hash does not match calculation input")
        if snapshot_payload.get("snapshot_id") != reference.snapshot_id:
            raise ValueError("snapshot ID does not match calculation reference")
        counterfactual_sources = tuple(
            source
            for source in reference.created_from
            if source.evidence_kind == EvidenceKind.COUNTERFACTUAL
        )
        if counterfactual_sources:
            counterfactual_payload = artifact.input_payload.get("counterfactual")
            if not isinstance(counterfactual_payload, dict):
                raise ValueError("counterfactual source requires a counterfactual input")
            if any(
                hash_counterfactual(counterfactual_payload, self.config) != source.content_hash
                for source in counterfactual_sources
            ):
                raise ValueError("counterfactual source hash does not match calculation input")
        calculation_sources = tuple(
            source
            for source in reference.created_from
            if source.evidence_kind == EvidenceKind.TACTICAL_CALCULATION
        )
        for source in calculation_sources:
            upstream = self._calculations.get(source.calculation_id or source.reference_id)
            if upstream is None:
                raise ValueError(f"upstream calculation is not registered: {source.reference_id}")
            if upstream.reference.output_hash != source.content_hash:
                raise ValueError(f"upstream calculation hash mismatch: {source.reference_id}")
        identity_hash = stable_hash(
            {
                "calculation_kind": reference.calculation_kind,
                "input_hash": reference.input_hash,
                "output_hash": reference.output_hash,
                "model_version": reference.model_version,
                "configuration_version": reference.configuration_version,
                "schema_version": reference.schema_version,
            },
            self.config,
        )
        expected_suffix = identity_hash[: self.config.calculation_id_hash_length]
        if not reference.calculation_id.endswith(expected_suffix):
            raise ValueError("calculation ID does not match artifact content")

    def _propagate(
        self,
        item_id: str,
        state: ValidityState,
        reason: str,
    ) -> tuple[str, ...]:
        if not self._item_exists(item_id):
            raise KeyError(f"evidence item not found: {item_id}")
        affected = (item_id, *self.graph.list_dependents(item_id, transitive=True))
        for affected_id in affected:
            self._apply_validity(affected_id, state, reason)
        return tuple(dict.fromkeys(affected))

    def _apply_validity(self, item_id: str, state: ValidityState, reason: str) -> None:
        previous = self._validity_of(item_id)
        if previous is None or previous == state:
            return
        if item_id in self._evidence:
            self._evidence[item_id] = self._evidence[item_id].model_copy(
                update={"validity_state": state}
            )
        if item_id in self._calculations:
            artifact = self._calculations[item_id]
            self._calculations[item_id] = artifact.model_copy(
                update={
                    "reference": artifact.reference.model_copy(
                        update={"validity_state": state}
                    )
                }
            )
        claim_id = self._claim_reference_ids.get(item_id, item_id)
        if claim_id in self._claims:
            record = self._claims[claim_id]
            verification_status = (
                VerificationStatus.STALE
                if state == ValidityState.STALE
                else VerificationStatus.REJECTED
            )
            self._claims[claim_id] = record.model_copy(
                update={
                    "evidence": record.evidence.model_copy(
                        update={
                            "validity_state": state,
                            "verification_status": verification_status,
                            "verification_reason": reason,
                        }
                    )
                }
            )
        self._audit_log.append(
            ValidityTransition(
                sequence=len(self._audit_log) + 1,
                item_id=item_id,
                previous_state=previous,
                new_state=state,
                reason=reason,
            )
        )

    def _validity_of(self, item_id: str) -> ValidityState | None:
        if item_id in self._evidence:
            return self._evidence[item_id].validity_state
        if item_id in self._calculations:
            return self._calculations[item_id].reference.validity_state
        claim_id = self._claim_reference_ids.get(item_id, item_id)
        if claim_id in self._claims:
            return self._claims[claim_id].evidence.validity_state
        return None

    def _item_exists(self, item_id: str) -> bool:
        return (
            item_id in self._evidence
            or item_id in self._calculations
            or item_id in self._claims
            or item_id in self._claim_reference_ids
        )


def _claim_snapshot_id(claim: ClaimEvidence) -> str | None:
    snapshot_ids = {
        reference.snapshot_id
        for reference in (*claim.evidence_references, *claim.calculation_references)
        if reference.snapshot_id is not None
    }
    return next(iter(snapshot_ids)) if len(snapshot_ids) == 1 else None
