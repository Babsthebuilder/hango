from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.evidence.models import CalculationArtifact, ClaimEvidence, ClaimType
from app.evidence.registry import InMemoryEvidenceRegistry
from app.evidence.verification import ClaimVerifier
from app.explanations.analyst import GroundingPacket
from app.explanations.models import (
    EvidenceCitation,
    ExplanationRequest,
    ExplanationSentence,
    PublicationState,
)
from app.explanations.providers import ExplanationProvider, LocalTemplateProvider
from app.explanations.registry import InMemoryExplanationRegistry
from app.explanations.service import ExplanationService


class FixedProvider(ExplanationProvider):
    provider_id = "fixed-test"
    provider_version = "fixed-test-v1"

    def __init__(self, text: str, *, numeric_value: float | None = None) -> None:
        self.text = text
        self.numeric_value = numeric_value

    def compose(self, packet: GroundingPacket) -> tuple[ExplanationSentence, ...]:
        claim = packet.claims[0].evidence
        if self.numeric_value is None:
            citation = EvidenceCitation(
                citation_id="citation-01",
                sentence_id="sentence-01",
                claim_id=claim.claim_id,
            )
        else:
            assertion = claim.numerical_assertions[0]
            citation = EvidenceCitation(
                citation_id="citation-01",
                sentence_id="sentence-01",
                claim_id=claim.claim_id,
                calculation_id=assertion.calculation_id,
                field_path=assertion.field_path,
                unit=assertion.unit,
                numeric_value=self.numeric_value,
            )
        return (
            ExplanationSentence(
                sentence_id="sentence-01",
                text=self.text,
                citations=(citation,),
            ),
        )


class FailingProvider(ExplanationProvider):
    provider_id = "failing-test"
    provider_version = "failing-test-v1"

    def compose(self, packet: GroundingPacket) -> tuple[ExplanationSentence, ...]:
        raise RuntimeError("provider unavailable")


def make_service(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
    provider: ExplanationProvider,
) -> tuple[ExplanationService, InMemoryEvidenceRegistry, ExplanationRequest]:
    evidence_registry = InMemoryEvidenceRegistry()
    evidence_registry.store_calculation(evidence_artifact)
    evidence_registry.store_claim(supported_claim)
    decision = ClaimVerifier(evidence_registry).verify(supported_claim)
    assert decision.status == "SUPPORTED"
    service = ExplanationService(
        evidence_registry,
        InMemoryExplanationRegistry(),
        (provider,),
    )
    request = ExplanationRequest(
        request_id="explanation-request-01",
        calculation_ids=(evidence_artifact.reference.calculation_id,),
        claim_ids=(supported_claim.claim_id,),
        provider_id=provider.provider_id,
    )
    return service, evidence_registry, request


def test_local_provider_generates_publishable_interpretation(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    service, _, request = make_service(
        evidence_artifact,
        supported_claim,
        LocalTemplateProvider(),
    )

    artifact = service.generate(request)

    assert artifact.draft.evidence_classification == "INTERPRETATION"
    assert artifact.verification.status == "SUPPORTED"
    assert artifact.verification.publishable is True
    assert artifact.publication_state == PublicationState.READY
    assert artifact.draft.sentences[0].citations[0].field_path == "opportunity_score"


def test_unsupported_number_is_rejected(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    provider = FixedProvider("The modeled opportunity value was 0.900000.", numeric_value=0.9)
    service, _, request = make_service(evidence_artifact, supported_claim, provider)

    artifact = service.generate(request)

    assert artifact.verification.status == "REJECTED"
    assert artifact.verification.publishable is False
    assert "not asserted" in artifact.verification.reason
    assert artifact.publication_state == PublicationState.BLOCKED


def test_display_rounding_remains_grounded_in_exact_citation(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    value = supported_claim.numerical_assertions[0].value
    provider = FixedProvider(
        f"The modeled opportunity value was {value:.6f}.",
        numeric_value=value,
    )
    service, _, request = make_service(evidence_artifact, supported_claim, provider)

    artifact = service.generate(request)

    assert artifact.verification.status == "SUPPORTED"
    assert artifact.verification.publishable is True


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("This created a 34% chance of a goal.", "probability"),
        ("The movement increased xT.", "xT"),
        ("The support player caused the route to open.", "causality"),
    ],
)
def test_overclaiming_is_rejected(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
    text: str,
    reason: str,
) -> None:
    provider = FixedProvider(text)
    service, _, request = make_service(evidence_artifact, supported_claim, provider)

    artifact = service.generate(request)

    assert artifact.verification.status == "REJECTED"
    assert reason.lower() in artifact.verification.reason.lower()


def test_upstream_staleness_blocks_publication(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    service, evidence_registry, request = make_service(
        evidence_artifact,
        supported_claim,
        LocalTemplateProvider(),
    )
    artifact = service.generate(request)
    evidence_registry.mark_stale(
        evidence_artifact.reference.calculation_id,
        "model superseded",
    )

    refreshed = service.verify(artifact.explanation_id)

    assert refreshed.verification.status == "STALE"
    assert refreshed.publication_state == PublicationState.STALE
    assert refreshed.validity_state == "STALE"


def test_explicitly_qualified_source_can_support_qualified_publication(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    qualified_claim = supported_claim.model_copy(
        update={
            "claim_id": "qualified-association",
            "claim_text": "The movement caused the tactical difference.",
        }
    )
    evidence_registry = InMemoryEvidenceRegistry()
    evidence_registry.store_calculation(evidence_artifact)
    evidence_registry.store_claim(qualified_claim)
    assert ClaimVerifier(evidence_registry).verify(qualified_claim).status == "QUALIFIED"
    provider = FixedProvider(
        "The positional change was associated with the modeled tactical difference."
    )
    service = ExplanationService(
        evidence_registry,
        InMemoryExplanationRegistry(),
        (provider,),
    )
    request = ExplanationRequest(
        request_id="qualified-request",
        calculation_ids=(evidence_artifact.reference.calculation_id,),
        claim_ids=(qualified_claim.claim_id,),
        provider_id=provider.provider_id,
    )

    artifact = service.generate(request)

    assert artifact.verification.status == "QUALIFIED"
    assert artifact.verification.publishable is True
    assert artifact.publication_state == PublicationState.READY


def test_interpretive_claim_cannot_be_reused_as_authoritative_evidence(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    interpretive_claim = supported_claim.model_copy(
        update={
            "claim_id": "generated-interpretation",
            "claim_text": "The shape appears tactically useful.",
            "claim_type": ClaimType.INTERPRETATION,
            "evidence_classification": ClaimType.INTERPRETATION,
            "numerical_assertions": (),
        }
    )
    evidence_registry = InMemoryEvidenceRegistry()
    evidence_registry.store_calculation(evidence_artifact)
    evidence_registry.store_claim(interpretive_claim)
    ClaimVerifier(evidence_registry).verify(interpretive_claim)
    provider = FixedProvider("The shape appears tactically useful.")
    service = ExplanationService(
        evidence_registry,
        InMemoryExplanationRegistry(),
        (provider,),
    )
    request = ExplanationRequest(
        request_id="generated-prose-request",
        calculation_ids=(evidence_artifact.reference.calculation_id,),
        claim_ids=(interpretive_claim.claim_id,),
        provider_id=provider.provider_id,
    )

    artifact = service.generate(request)

    assert artifact.verification.status == "REJECTED"
    assert "cannot serve as evidence" in artifact.verification.reason


def test_sentence_contract_rejects_missing_citations() -> None:
    with pytest.raises(ValidationError):
        ExplanationSentence(
            sentence_id="sentence-01",
            text="Unsupported generated prose.",
            citations=(),
        )


def test_provider_failure_is_not_converted_to_evidence(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    service, _, request = make_service(
        evidence_artifact,
        supported_claim,
        FailingProvider(),
    )

    with pytest.raises(RuntimeError, match="provider unavailable"):
        service.generate(request)
