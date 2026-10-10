"""Application service coordinating Analyst, Narrator, and Editorial Verifier."""

from __future__ import annotations

from app.evidence.hashing import stable_hash
from app.evidence.models import ValidityState, VerificationStatus
from app.evidence.registry import InMemoryEvidenceRegistry
from app.explanations.analyst import EvidenceAnalyst
from app.explanations.models import (
    ExplanationArtifact,
    ExplanationRequest,
    PublicationState,
)
from app.explanations.narrator import EvidenceNarrator
from app.explanations.providers import ExplanationProvider
from app.explanations.registry import InMemoryExplanationRegistry
from app.explanations.verification import EditorialVerifier


class ExplanationService:
    """Run the role-separated explanation workflow."""

    def __init__(
        self,
        evidence_registry: InMemoryEvidenceRegistry,
        explanation_registry: InMemoryExplanationRegistry,
        providers: tuple[ExplanationProvider, ...],
    ) -> None:
        self.evidence_registry = evidence_registry
        self.explanation_registry = explanation_registry
        self.providers = {provider.provider_id: provider for provider in providers}
        self.analyst = EvidenceAnalyst(evidence_registry)
        self.verifier = EditorialVerifier(evidence_registry)

    def generate(self, request: ExplanationRequest) -> ExplanationArtifact:
        try:
            provider = self.providers[request.provider_id]
        except KeyError as error:
            message = f"explanation provider is not configured: {request.provider_id}"
            raise ValueError(message) from error
        packet = self.analyst.assemble(request)
        draft = EvidenceNarrator(provider).compose(packet)
        identity = stable_hash({"request": request, "draft": draft})
        explanation_id = f"explanation:{identity[:20]}"
        decision = self.verifier.verify(explanation_id, request, draft)
        validity = _validity_for(decision.status, decision.reason)
        artifact = ExplanationArtifact(
            explanation_id=explanation_id,
            request=request,
            draft=draft,
            verification=decision,
            verification_history=(decision,),
            publication_state=_publication_for(decision.status, validity),
            validity_state=validity,
        )
        return self.explanation_registry.store(artifact)

    def get(self, explanation_id: str, *, refresh: bool = True) -> ExplanationArtifact:
        artifact = self.explanation_registry.get(explanation_id)
        if refresh and artifact.validity_state != ValidityState.INVALIDATED:
            return self.verify(explanation_id)
        return artifact

    def verify(self, explanation_id: str) -> ExplanationArtifact:
        artifact = self.explanation_registry.get(explanation_id)
        if artifact.validity_state == ValidityState.INVALIDATED:
            return artifact
        result = self.verifier.verify(
            explanation_id,
            artifact.request,
            artifact.draft,
        )
        return self.explanation_registry.record_verification(explanation_id, result)

    def invalidate(self, explanation_id: str, reason: str) -> ExplanationArtifact:
        return self.explanation_registry.invalidate(explanation_id, reason)


def _validity_for(status: VerificationStatus, reason: str) -> ValidityState:
    if status == VerificationStatus.STALE:
        return ValidityState.STALE
    if status == VerificationStatus.REJECTED and "invalidated" in reason:
        return ValidityState.INVALIDATED
    return ValidityState.VALID


def _publication_for(
    status: VerificationStatus,
    validity: ValidityState,
) -> PublicationState:
    if validity == ValidityState.INVALIDATED:
        return PublicationState.INVALIDATED
    if status == VerificationStatus.STALE:
        return PublicationState.STALE
    if status in {VerificationStatus.SUPPORTED, VerificationStatus.QUALIFIED}:
        return PublicationState.READY
    return PublicationState.BLOCKED
