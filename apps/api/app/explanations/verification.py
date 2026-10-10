"""Deterministic editorial verifier for generated explanations."""

from __future__ import annotations

import math
import re
from typing import Any

from app.evidence.models import ClaimType, ValidityState, VerificationStatus
from app.evidence.registry import InMemoryEvidenceRegistry
from app.evidence.verification import ClaimVerifier
from app.explanations.models import (
    EditorialVerificationResult,
    ExplanationDraft,
    ExplanationRequest,
)

_NUMBER = re.compile(r"(?<![A-Za-z0-9_])[-+]?\d+(?:\.\d+)?(?![A-Za-z0-9_])")
_PROBABILITY = re.compile(
    r"(?:\bprobability\b|\bgoal chance\b|\bchance of (?:a )?goal\b|\d+(?:\.\d+)?\s*%)",
    re.IGNORECASE,
)
_XT_TERM = re.compile(r"(?:\bxT\b|expected threat)", re.IGNORECASE)
_CAUSAL_OR_INTENT = re.compile(
    r"(?:\bcaused\b|\btherefore\b|\bled to\b|\bresulted in\b|\bbecause\b|"
    r"\bforced\b|\bintended\b|\bwanted\b|\bdeliberately\b|\bdragged\b)",
    re.IGNORECASE,
)


class EditorialVerifier:
    """Recheck source evidence, citations, and wording before publication."""

    def __init__(self, evidence_registry: InMemoryEvidenceRegistry) -> None:
        self.evidence_registry = evidence_registry

    def verify(
        self,
        explanation_id: str,
        request: ExplanationRequest,
        draft: ExplanationDraft,
    ) -> EditorialVerificationResult:
        checked_claims: list[str] = []
        checked_calculations: list[str] = []
        source_statuses: list[VerificationStatus] = []

        if draft.evidence_classification != "INTERPRETATION":
            return self._result(
                explanation_id,
                VerificationStatus.REJECTED,
                "Generated prose must remain classified as INTERPRETATION",
            )
        if draft.request_id != request.request_id:
            return self._result(
                explanation_id,
                VerificationStatus.REJECTED,
                "Draft request identity does not match its grounding request",
            )

        for claim_id in request.claim_ids:
            checked_claims.append(claim_id)
            try:
                record = self.evidence_registry.get_claim(claim_id)
            except KeyError:
                return self._result(
                    explanation_id,
                    VerificationStatus.REJECTED,
                    f"Referenced claim does not exist: {claim_id}",
                    checked_claims,
                    checked_calculations,
                )
            if record.evidence.validity_state == ValidityState.INVALIDATED:
                return self._result(
                    explanation_id,
                    VerificationStatus.REJECTED,
                    f"Referenced claim is invalidated: {claim_id}",
                    checked_claims,
                    checked_calculations,
                )
            if record.evidence.claim_type == ClaimType.INTERPRETATION:
                return self._result(
                    explanation_id,
                    VerificationStatus.REJECTED,
                    f"Generated or interpretive prose cannot serve as evidence: {claim_id}",
                    checked_claims,
                    checked_calculations,
                )
            decision = ClaimVerifier(self.evidence_registry).verify(record.evidence)
            source_statuses.append(decision.status)
            if decision.status == VerificationStatus.STALE:
                return self._result(
                    explanation_id,
                    VerificationStatus.STALE,
                    f"Referenced claim is stale: {claim_id}",
                    checked_claims,
                    checked_calculations,
                )
            if decision.status == VerificationStatus.REJECTED:
                return self._result(
                    explanation_id,
                    VerificationStatus.REJECTED,
                    f"Referenced claim is rejected: {claim_id}",
                    checked_claims,
                    checked_calculations,
                )

        for calculation_id in request.calculation_ids:
            checked_calculations.append(calculation_id)
            try:
                artifact = self.evidence_registry.get_calculation(calculation_id)
            except KeyError:
                return self._result(
                    explanation_id,
                    VerificationStatus.REJECTED,
                    f"Referenced calculation does not exist: {calculation_id}",
                    checked_claims,
                    checked_calculations,
                )
            if artifact.reference.validity_state == ValidityState.STALE:
                return self._result(
                    explanation_id,
                    VerificationStatus.STALE,
                    f"Referenced calculation is stale: {calculation_id}",
                    checked_claims,
                    checked_calculations,
                )
            if artifact.reference.validity_state == ValidityState.INVALIDATED:
                return self._result(
                    explanation_id,
                    VerificationStatus.REJECTED,
                    f"Referenced calculation is invalidated: {calculation_id}",
                    checked_claims,
                    checked_calculations,
                )

        requested_claims = set(request.claim_ids)
        requested_calculations = set(request.calculation_ids)
        for sentence in draft.sentences:
            wording_error = self._wording_error(sentence.text)
            if wording_error is not None:
                return self._result(
                    explanation_id,
                    VerificationStatus.REJECTED,
                    wording_error,
                    checked_claims,
                    checked_calculations,
                    [sentence.sentence_id],
                )
            if not sentence.citations:
                return self._result(
                    explanation_id,
                    VerificationStatus.REJECTED,
                    "Every explanation sentence requires registered evidence",
                    checked_claims,
                    checked_calculations,
                    [sentence.sentence_id],
                )
            citation_error = self._verify_citations(
                sentence.text,
                sentence.citations,
                requested_claims,
                requested_calculations,
            )
            if citation_error is not None:
                return self._result(
                    explanation_id,
                    VerificationStatus.REJECTED,
                    citation_error,
                    checked_claims,
                    checked_calculations,
                    [sentence.sentence_id],
                )

        status = (
            VerificationStatus.QUALIFIED
            if VerificationStatus.QUALIFIED in source_statuses
            else VerificationStatus.SUPPORTED
        )
        reason = (
            "Explanation is grounded but inherits an explicit source qualification"
            if status == VerificationStatus.QUALIFIED
            else "Every sentence and numerical statement is grounded in current evidence"
        )
        return self._result(
            explanation_id,
            status,
            reason,
            checked_claims,
            checked_calculations,
        )

    def _verify_citations(
        self,
        sentence_text: str,
        citations: tuple[Any, ...],
        requested_claims: set[str],
        requested_calculations: set[str],
    ) -> str | None:
        cited_numbers: list[float] = []
        for citation in citations:
            if citation.claim_id not in requested_claims:
                return f"Citation uses an unrequested claim: {citation.claim_id}"
            try:
                claim = self.evidence_registry.get_claim(citation.claim_id).evidence
            except KeyError:
                return f"Citation claim does not exist: {citation.claim_id}"
            if citation.numeric_value is None:
                continue
            if citation.calculation_id not in requested_calculations:
                return (
                    "Citation uses an unrequested calculation: "
                    f"{citation.calculation_id}"
                )
            assertion_matches = any(
                assertion.calculation_id == citation.calculation_id
                and assertion.field_path == citation.field_path
                and assertion.unit == citation.unit
                and math.isclose(
                    assertion.value,
                    citation.numeric_value,
                    rel_tol=1e-9,
                    abs_tol=1e-9,
                )
                for assertion in claim.numerical_assertions
            )
            if not assertion_matches:
                return "Citation is not asserted by its referenced verified claim"
            artifact = self.evidence_registry.get_calculation(citation.calculation_id)
            if artifact.numerical_units.get(citation.field_path or "") != citation.unit:
                return f"Citation unit does not match evidence: {citation.field_path}"
            try:
                authoritative = _resolve_path(
                    artifact.authoritative_output,
                    citation.field_path or "",
                )
            except (KeyError, IndexError, TypeError, ValueError):
                return f"Citation path does not exist: {citation.field_path}"
            if not isinstance(authoritative, (int, float)) or isinstance(authoritative, bool):
                return f"Citation path is not numeric: {citation.field_path}"
            if not math.isclose(
                float(authoritative),
                citation.numeric_value,
                rel_tol=1e-9,
                abs_tol=1e-9,
            ):
                return f"Citation value does not match evidence: {citation.field_path}"
            cited_numbers.append(citation.numeric_value)

        for token in _NUMBER.findall(sentence_text):
            value = float(token)
            if not any(
                _matches_display_precision(value, cited, token)
                for cited in cited_numbers
            ):
                return f"Numerical statement lacks an authoritative citation: {token}"
        return None

    @staticmethod
    def _wording_error(text: str) -> str | None:
        if _PROBABILITY.search(text):
            return "No calibrated probability model supports probability wording"
        if _XT_TERM.search(text):
            return "Linear pitch value and route opportunity must not be presented as xT"
        if _CAUSAL_OR_INTENT.search(text):
            return "Deterministic positional evidence does not prove causality or player intent"
        return None

    @staticmethod
    def _result(
        explanation_id: str,
        status: VerificationStatus,
        reason: str,
        checked_claims: list[str] | None = None,
        checked_calculations: list[str] | None = None,
        offending_sentences: list[str] | None = None,
    ) -> EditorialVerificationResult:
        return EditorialVerificationResult(
            explanation_id=explanation_id,
            status=status,
            publishable=status
            in {VerificationStatus.SUPPORTED, VerificationStatus.QUALIFIED},
            reason=reason,
            checked_claim_ids=tuple(checked_claims or ()),
            checked_calculation_ids=tuple(checked_calculations or ()),
            offending_sentence_ids=tuple(offending_sentences or ()),
        )


def _resolve_path(payload: dict[str, Any], field_path: str) -> Any:
    current: Any = payload
    for segment in field_path.split("."):
        if isinstance(current, dict):
            current = current[segment]
        elif isinstance(current, (list, tuple)):
            current = current[int(segment)]
        else:
            raise TypeError(f"cannot traverse {segment}")
    return current


def _matches_display_precision(displayed: float, authoritative: float, token: str) -> bool:
    """Allow explicit decimal rounding while retaining exact authoritative citations."""

    decimal_places = len(token.partition(".")[2]) if "." in token else 0
    rounding_tolerance = 0.5 * (10 ** -decimal_places) if decimal_places else 1e-9
    return math.isclose(
        displayed,
        authoritative,
        rel_tol=1e-9,
        abs_tol=max(1e-9, rounding_tolerance),
    )
