"""Compatibility imports for evidence contracts now owned by ``app.evidence``."""

from app.evidence.models import (
    CalculationReference,
    ClaimEvidence,
    ClaimType,
    VerificationStatus,
)

PublicationStatus = VerificationStatus

__all__ = [
    "CalculationReference",
    "ClaimEvidence",
    "ClaimType",
    "PublicationStatus",
]
