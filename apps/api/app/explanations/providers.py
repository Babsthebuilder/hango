"""Narrative provider boundary and deterministic local implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.explanations.analyst import GroundingPacket
from app.explanations.models import EvidenceCitation, ExplanationSentence


class ExplanationProvider(ABC):
    """Provider interface; providers return prose and citations, never decisions."""

    provider_id: str
    provider_version: str

    @abstractmethod
    def compose(self, packet: GroundingPacket) -> tuple[ExplanationSentence, ...]: ...


class LocalTemplateProvider(ExplanationProvider):
    """Deterministic offline provider used for development and tests."""

    provider_id = "local-template-v0.1"
    provider_version = "local-template-v0.1"

    def compose(self, packet: GroundingPacket) -> tuple[ExplanationSentence, ...]:
        sentences: list[ExplanationSentence] = []
        for index, record in enumerate(packet.claims, start=1):
            claim = record.evidence
            sentence_id = f"sentence-{index:02d}"
            citations = tuple(
                EvidenceCitation(
                    citation_id=f"{sentence_id}-numeric-{assertion_index:02d}",
                    sentence_id=sentence_id,
                    claim_id=claim.claim_id,
                    calculation_id=assertion.calculation_id,
                    field_path=assertion.field_path,
                    unit=assertion.unit,
                    numeric_value=assertion.value,
                )
                for assertion_index, assertion in enumerate(
                    claim.numerical_assertions,
                    start=1,
                )
            )
            if not citations:
                citations = (
                    EvidenceCitation(
                        citation_id=f"{sentence_id}-claim-01",
                        sentence_id=sentence_id,
                        claim_id=claim.claim_id,
                    ),
                )
            sentences.append(
                ExplanationSentence(
                    sentence_id=sentence_id,
                    text=claim.claim_text,
                    citations=citations,
                )
            )
        return tuple(sentences)
