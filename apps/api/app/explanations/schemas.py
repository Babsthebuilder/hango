"""Typed HTTP contracts for explanation lifecycle operations."""

from pydantic import Field

from app.evidence.models import EvidenceModel
from app.explanations.models import ExplanationArtifact


class ExplanationDetails(EvidenceModel):
    artifact: ExplanationArtifact


class ExplanationLifecycleRequest(EvidenceModel):
    reason: str = Field(min_length=1)
