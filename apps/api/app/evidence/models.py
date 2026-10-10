"""Typed contracts for HANGO evidence, claims, replay, and verification."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvidenceModel(BaseModel):
    """Immutable evidence model with finite floating-point values."""

    model_config = ConfigDict(frozen=True, allow_inf_nan=False)


class ClaimType(StrEnum):
    """Epistemic classification for a claim."""

    OBSERVED = "OBSERVED"
    CALCULATED = "CALCULATED"
    MODEL_ESTIMATE = "MODEL_ESTIMATE"
    INTERPRETATION = "INTERPRETATION"


class VerificationStatus(StrEnum):
    """Deterministic publication outcome."""

    SUPPORTED = "SUPPORTED"
    QUALIFIED = "QUALIFIED"
    REJECTED = "REJECTED"
    STALE = "STALE"


class ValidityState(StrEnum):
    """Lifecycle state, independent from publication status."""

    VALID = "VALID"
    STALE = "STALE"
    INVALIDATED = "INVALIDATED"


class EvidenceKind(StrEnum):
    """Kinds of objects that can participate in the trust chain."""

    SNAPSHOT = "SNAPSHOT"
    COUNTERFACTUAL = "COUNTERFACTUAL"
    TACTICAL_CALCULATION = "TACTICAL_CALCULATION"
    CLAIM_EVIDENCE = "CLAIM_EVIDENCE"
    CLAIM_RECORD = "CLAIM_RECORD"
    GENERATED_PROSE = "GENERATED_PROSE"


class CalculationKind(StrEnum):
    """Replayable deterministic tactical operations."""

    SNAPSHOT_ANALYSIS = "SNAPSHOT_ANALYSIS"
    TRIANGLE_ANALYSIS = "TRIANGLE_ANALYSIS"
    INTERACTION = "INTERACTION"


class EvidenceReference(EvidenceModel):
    """Stable pointer to authoritative semantic evidence."""

    reference_id: str = Field(min_length=1)
    evidence_kind: EvidenceKind
    object_id: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    snapshot_id: str | None = None
    calculation_id: str | None = None
    model_version: str | None = None
    source_provenance: str = Field(min_length=1)
    validity_state: ValidityState = ValidityState.VALID
    schema_version: str = Field(min_length=1)


class DependencyReference(EvidenceModel):
    """Directed dependency from one evidence item to an upstream item."""

    dependent_id: str = Field(min_length=1)
    dependency_id: str = Field(min_length=1)
    relationship: str = Field(default="CREATED_FROM", min_length=1)

    @model_validator(mode="after")
    def reject_self_dependency(self) -> DependencyReference:
        if self.dependent_id == self.dependency_id:
            raise ValueError("evidence cannot depend on itself")
        return self


class CalculationReference(EvidenceModel):
    """Versioned identity for one deterministic calculation."""

    calculation_id: str = Field(pattern=r"^calc:[a-z0-9_-]+:[0-9a-f]{16,64}$")
    calculation_kind: CalculationKind
    input_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    snapshot_id: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    configuration_version: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    created_from: tuple[EvidenceReference, ...] = Field(min_length=1)
    validity_state: ValidityState = ValidityState.VALID


class CalculationArtifact(EvidenceModel):
    """Authoritative inputs, output, configuration, and identity for replay."""

    reference: CalculationReference
    input_payload: dict[str, Any]
    authoritative_output: dict[str, Any]
    configuration_payload: dict[str, Any]
    numerical_units: dict[str, str] = Field(default_factory=dict)


class NumericalAssertion(EvidenceModel):
    """One claimed number tied to a calculation output path and unit."""

    calculation_id: str = Field(min_length=1)
    field_path: str = Field(min_length=1)
    value: float
    unit: str = Field(min_length=1)


class ClaimEvidence(EvidenceModel):
    """First-class evidence bundle for one proposed narrative claim."""

    claim_id: str = Field(min_length=1)
    claim_text: str = Field(min_length=1)
    claim_type: ClaimType
    evidence_classification: ClaimType
    evidence_references: tuple[EvidenceReference, ...] = ()
    numerical_assertions: tuple[NumericalAssertion, ...] = ()
    calculation_references: tuple[CalculationReference, ...] = ()
    model_version: str = Field(min_length=1)
    verification_status: VerificationStatus = VerificationStatus.STALE
    verification_reason: str = Field(default="Not yet verified", min_length=1)
    created_from: tuple[str, ...] = ()
    validity_state: ValidityState = ValidityState.VALID
    schema_version: str = Field(min_length=1)


class NumericDifference(EvidenceModel):
    """Tolerance-aware comparison for one numeric output path."""

    field_path: str
    expected: float
    actual: float
    absolute_difference: float = Field(ge=0.0)
    within_tolerance: bool


class ReplayResult(EvidenceModel):
    """Structured deterministic replay comparison."""

    calculation_id: str
    replay_success: bool
    expected_output_hash: str
    actual_output_hash: str | None
    numeric_differences: tuple[NumericDifference, ...] = ()
    version_match: bool
    configuration_match: bool
    stale_dependencies: tuple[str, ...] = ()
    explanation: str


class VerificationResult(EvidenceModel):
    """Authoritative claim-verification decision."""

    claim_id: str
    status: VerificationStatus
    reason: str
    replay_results: tuple[ReplayResult, ...] = ()
    checked_evidence_ids: tuple[str, ...] = ()
    suggested_claim_text: str | None = None


class ClaimRecord(EvidenceModel):
    """Stored claim plus append-only deterministic verification history."""

    record_id: str = Field(min_length=1)
    evidence: ClaimEvidence
    verification_history: tuple[VerificationResult, ...] = ()
    supersedes: str | None = None


class ValidityTransition(EvidenceModel):
    """Audit entry for a lifecycle transition without transient timestamps."""

    sequence: int = Field(ge=1)
    item_id: str
    previous_state: ValidityState
    new_state: ValidityState
    reason: str
