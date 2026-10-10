"""Narrator boundary that delegates prose composition to a provider."""

from app.evidence.hashing import stable_hash
from app.explanations.analyst import GroundingPacket
from app.explanations.models import ExplanationDraft
from app.explanations.providers import ExplanationProvider


class EvidenceNarrator:
    """Compose an INTERPRETATION draft without assigning publication status."""

    def __init__(self, provider: ExplanationProvider) -> None:
        self.provider = provider

    def compose(self, packet: GroundingPacket) -> ExplanationDraft:
        sentences = self.provider.compose(packet)
        identity = stable_hash(
            {
                "request": packet.request,
                "sentences": sentences,
                "provider_id": self.provider.provider_id,
                "provider_version": self.provider.provider_version,
            }
        )
        return ExplanationDraft(
            draft_id=f"draft:{identity[:20]}",
            request_id=packet.request.request_id,
            sentences=sentences,
            evidence_classification="INTERPRETATION",
            provider_id=self.provider.provider_id,
            provider_version=self.provider.provider_version,
        )
