"""Read-only Analyst boundary for retrieving registered evidence."""

from __future__ import annotations

from dataclasses import dataclass

from app.evidence.models import CalculationArtifact, ClaimRecord
from app.evidence.registry import InMemoryEvidenceRegistry
from app.explanations.models import ExplanationRequest


@dataclass(frozen=True)
class GroundingPacket:
    """Registered evidence supplied to a narrator without new calculations."""

    request: ExplanationRequest
    calculations: tuple[CalculationArtifact, ...]
    claims: tuple[ClaimRecord, ...]


class EvidenceAnalyst:
    """Retrieve existing artifacts; never derive tactical metrics."""

    def __init__(self, registry: InMemoryEvidenceRegistry) -> None:
        self.registry = registry

    def assemble(self, request: ExplanationRequest) -> GroundingPacket:
        calculations = tuple(
            self.registry.get_calculation(calculation_id)
            for calculation_id in request.calculation_ids
        )
        claims = tuple(self.registry.get_claim(claim_id) for claim_id in request.claim_ids)
        return GroundingPacket(request=request, calculations=calculations, claims=claims)
