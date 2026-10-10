"""Audit-preserving local registry for explanation artifacts."""

from __future__ import annotations

from app.evidence.models import ValidityState, VerificationStatus
from app.explanations.models import (
    EditorialVerificationResult,
    ExplanationArtifact,
    PublicationState,
)


class InMemoryExplanationRegistry:
    """Replaceable in-memory persistence boundary for Phase 5."""

    def __init__(self) -> None:
        self._artifacts: dict[str, ExplanationArtifact] = {}

    def store(self, artifact: ExplanationArtifact) -> ExplanationArtifact:
        existing = self._artifacts.get(artifact.explanation_id)
        if existing is not None:
            if existing.request != artifact.request or existing.draft != artifact.draft:
                raise ValueError("explanation ID collision with different semantic content")
            if existing.validity_state == ValidityState.INVALIDATED:
                return existing
            return self.record_verification(
                artifact.explanation_id,
                artifact.verification,
            )
        self._artifacts[artifact.explanation_id] = artifact
        return artifact

    def get(self, explanation_id: str) -> ExplanationArtifact:
        try:
            return self._artifacts[explanation_id]
        except KeyError as error:
            raise KeyError(f"explanation not found: {explanation_id}") from error

    def record_verification(
        self,
        explanation_id: str,
        result: EditorialVerificationResult,
    ) -> ExplanationArtifact:
        artifact = self.get(explanation_id)
        history = artifact.verification_history
        if not history or history[-1] != result:
            history = (*history, result)
        validity = artifact.validity_state
        if result.status == VerificationStatus.STALE:
            validity = ValidityState.STALE
        elif result.status == VerificationStatus.REJECTED and "invalidated" in result.reason:
            validity = ValidityState.INVALIDATED
        updated = artifact.model_copy(
            update={
                "verification": result,
                "verification_history": history,
                "publication_state": _publication_state(result, validity),
                "validity_state": validity,
            }
        )
        self._artifacts[explanation_id] = updated
        return updated

    def invalidate(self, explanation_id: str, reason: str) -> ExplanationArtifact:
        artifact = self.get(explanation_id)
        result = EditorialVerificationResult(
            explanation_id=explanation_id,
            status=VerificationStatus.REJECTED,
            publishable=False,
            reason=f"Explanation invalidated: {reason}",
            checked_claim_ids=artifact.verification.checked_claim_ids,
            checked_calculation_ids=artifact.verification.checked_calculation_ids,
        )
        updated = artifact.model_copy(
            update={
                "verification": result,
                "verification_history": (*artifact.verification_history, result),
                "publication_state": PublicationState.INVALIDATED,
                "validity_state": ValidityState.INVALIDATED,
            }
        )
        self._artifacts[explanation_id] = updated
        return updated

    def clear(self) -> None:
        self._artifacts.clear()


def _publication_state(
    result: EditorialVerificationResult,
    validity: ValidityState,
) -> PublicationState:
    if validity == ValidityState.INVALIDATED:
        return PublicationState.INVALIDATED
    if result.status == VerificationStatus.STALE:
        return PublicationState.STALE
    if result.publishable:
        return PublicationState.READY
    return PublicationState.BLOCKED
