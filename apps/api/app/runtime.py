"""Process-local service registries shared by HTTP adapters."""

from app.evidence.registry import InMemoryEvidenceRegistry
from app.explanations.registry import InMemoryExplanationRegistry

evidence_registry = InMemoryEvidenceRegistry()
explanation_registry = InMemoryExplanationRegistry()
