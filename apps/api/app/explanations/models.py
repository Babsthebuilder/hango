"""Provider-neutral contracts for grounded explanation and editorial decisions."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from app.evidence.models import (
    ClaimType,
    EvidenceModel,
    ValidityState,
    VerificationStatus,
)

EXPLANATION_SCHEMA_VERSION = "explanation-schema-v0.1"


class PublicationState(StrEnum):
    """Editorial lifecycle, independent from evidence validity."""

    DRAFT = "DRAFT"
    READY = "READY"
    BLOCKED = "BLOCKED"
    STALE = "STALE"
    INVALIDATED = "INVALIDATED"


class ExplanationRequest(EvidenceModel):
    """Request for prose grounded in registered calculations and claims."""

    request_id: str = Field(min_length=1)
    calculation_ids: tuple[str, ...] = Field(min_length=1)
    claim_ids: tuple[str, ...] = Field(min_length=1)
    provider_id: str = "local-template-v0.1"
    audience: str = "editorial"
    schema_version: str = EXPLANATION_SCHEMA_VERSION

    @model_validator(mode="after")
    def reject_duplicate_sources(self) -> ExplanationRequest:
        if len(set(self.calculation_ids)) != len(self.calculation_ids):
            raise ValueError("calculation IDs must be unique")
        if len(set(self.claim_ids)) != len(self.claim_ids):
            raise ValueError("claim IDs must be unique")
        return self


class EvidenceCitation(EvidenceModel):
    """Sentence-level link to registered claim and calculation evidence."""

    citation_id: str = Field(min_length=1)
    sentence_id: str = Field(min_length=1)
    claim_id: str = Field(min_length=1)
    calculation_id: str | None = None
    field_path: str | None = None
    unit: str | None = None
    numeric_value: float | None = None

    @model_validator(mode="after")
    def require_complete_numeric_source(self) -> EvidenceCitation:
        numeric_parts = (
            self.calculation_id,
            self.field_path,
            self.unit,
            self.numeric_value,
        )
        if any(part is not None for part in numeric_parts) and not all(
            part is not None for part in numeric_parts
        ):
            raise ValueError(
                "numeric citations require calculation_id, field_path, unit, and numeric_value"
            )
        return self


class ExplanationSentence(EvidenceModel):
    """One editorial sentence with explicit supporting citations."""

    sentence_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    citations: tuple[EvidenceCitation, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def citation_sentence_ids_match(self) -> ExplanationSentence:
        if any(citation.sentence_id != self.sentence_id for citation in self.citations):
            raise ValueError("citation sentence_id must match its sentence")
        return self


class ExplanationDraft(EvidenceModel):
    """Narrator output; it carries no authority to approve itself."""

    draft_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    sentences: tuple[ExplanationSentence, ...] = Field(min_length=1)
    evidence_classification: ClaimType = ClaimType.INTERPRETATION
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    schema_version: str = EXPLANATION_SCHEMA_VERSION

    @model_validator(mode="after")
    def require_interpretation_classification(self) -> ExplanationDraft:
        if self.evidence_classification != ClaimType.INTERPRETATION:
            raise ValueError("generated explanation must be classified as INTERPRETATION")
        sentence_ids = tuple(sentence.sentence_id for sentence in self.sentences)
        if len(set(sentence_ids)) != len(sentence_ids):
            raise ValueError("sentence IDs must be unique")
        return self


class EditorialVerificationResult(EvidenceModel):
    """Deterministic publication decision made outside the narrator."""

    explanation_id: str = Field(min_length=1)
    status: VerificationStatus
    publishable: bool
    reason: str = Field(min_length=1)
    checked_claim_ids: tuple[str, ...] = ()
    checked_calculation_ids: tuple[str, ...] = ()
    offending_sentence_ids: tuple[str, ...] = ()
    schema_version: str = EXPLANATION_SCHEMA_VERSION

    @model_validator(mode="after")
    def restrict_publishable_status(self) -> EditorialVerificationResult:
        allowed = {VerificationStatus.SUPPORTED, VerificationStatus.QUALIFIED}
        if self.publishable != (self.status in allowed):
            raise ValueError("only SUPPORTED or QUALIFIED explanations are publishable")
        return self


class ExplanationArtifact(EvidenceModel):
    """Stored prose, grounding request, current decision, and audit history."""

    explanation_id: str = Field(pattern=r"^explanation:[0-9a-f]{20}$")
    request: ExplanationRequest
    draft: ExplanationDraft
    verification: EditorialVerificationResult
    verification_history: tuple[EditorialVerificationResult, ...] = Field(min_length=1)
    publication_state: PublicationState
    validity_state: ValidityState = ValidityState.VALID
    schema_version: str = EXPLANATION_SCHEMA_VERSION
