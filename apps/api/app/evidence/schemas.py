"""Typed HTTP boundary contracts for the evidence service."""

from __future__ import annotations

from typing import Any

from pydantic import model_validator

from app.evidence.models import (
    CalculationArtifact,
    ClaimEvidence,
    ClaimRecord,
    EvidenceModel,
)


class RegisterEvidenceRequest(EvidenceModel):
    calculation: CalculationArtifact | None = None
    claim: ClaimEvidence | None = None

    @model_validator(mode="after")
    def require_exactly_one_item(self) -> RegisterEvidenceRequest:
        if (self.calculation is None) == (self.claim is None):
            raise ValueError("provide exactly one calculation or claim")
        return self


class RegisterEvidenceResponse(EvidenceModel):
    item_id: str
    item_type: str


class CalculationDetails(EvidenceModel):
    artifact: CalculationArtifact
    dependencies: tuple[str, ...]
    dependents: tuple[str, ...]


class ClaimDetails(EvidenceModel):
    record: ClaimRecord
    dependencies: tuple[str, ...]
    dependents: tuple[str, ...]


class VerifyClaimRequest(EvidenceModel):
    claim_id: str | None = None
    claim: ClaimEvidence | None = None

    @model_validator(mode="after")
    def require_exactly_one_claim(self) -> VerifyClaimRequest:
        if (self.claim_id is None) == (self.claim is None):
            raise ValueError("provide exactly one claim_id or claim")
        return self


class ReplayCalculationRequest(EvidenceModel):
    calculation_id: str
    input_override: dict[str, Any] | None = None
    configuration_override: dict[str, Any] | None = None


class LifecycleRequest(EvidenceModel):
    evidence_id: str
    reason: str


class LifecycleResponse(EvidenceModel):
    affected_ids: tuple[str, ...]
