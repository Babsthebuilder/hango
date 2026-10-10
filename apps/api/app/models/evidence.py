"""Evidence and claim-publication contracts."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ClaimType(StrEnum):
    """Epistemic classification for every narrative claim."""

    OBSERVED = "OBSERVED"
    CALCULATED = "CALCULATED"
    MODEL_ESTIMATE = "MODEL_ESTIMATE"
    INTERPRETATION = "INTERPRETATION"


class PublicationStatus(StrEnum):
    """Evidence verification result."""

    SUPPORTED = "SUPPORTED"
    QUALIFIED = "QUALIFIED"
    REJECTED = "REJECTED"
    STALE = "STALE"


class CalculationReference(BaseModel):
    """Traceable reference to one deterministic calculation."""

    model_config = ConfigDict(frozen=True)

    calculation_id: str = Field(min_length=1)
    calculation_kind: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    snapshot_id: str = Field(min_length=1)
    input_hash: str = Field(min_length=1)


class ClaimEvidence(BaseModel):
    """Evidence carried with a publishable claim."""

    model_config = ConfigDict(frozen=True)

    claim_id: str = Field(min_length=1)
    claim_text: str = Field(min_length=1)
    claim_type: ClaimType
    publication_status: PublicationStatus
    calculation_references: tuple[CalculationReference, ...] = ()
    qualification: str | None = None
