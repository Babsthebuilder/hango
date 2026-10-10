"""Canonical serialization and SHA-256 hashing for semantic evidence content."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel

from app.evidence.config import DEFAULT_EVIDENCE_CONFIG, EvidenceConfig

_SEMANTIC_LIST_KEYS: dict[str, str] = {
    "players": "player_id",
    "evidence_references": "reference_id",
    "calculation_references": "calculation_id",
    "created_from": "reference_id",
    "defender_measurements": "defender_id",
}
_SEMANTIC_SORTED_LIST_KEYS = {
    "corridor_intruder_ids",
    "numerical_assertions",
    "rejection_reasons",
}
_NONSEMANTIC_CLAIM_KEYS = {
    "validity_state",
    "verification_reason",
    "verification_status",
}


def _float_string(value: float, decimal_places: int) -> str:
    if not math.isfinite(value):
        raise ValueError("canonical evidence cannot contain NaN or infinity")
    quantum = Decimal(1).scaleb(-decimal_places)
    normalized = Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_EVEN)
    if normalized == 0:
        normalized = abs(normalized)
    return f"{normalized:.{decimal_places}f}"


def _datetime_string(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("canonical datetimes must include a timezone")
    utc_value = value.astimezone(UTC)
    return utc_value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonical_value(
    value: Any,
    config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG,
    *,
    parent_key: str | None = None,
) -> Any:
    """Normalize supported values into deterministic JSON-compatible content."""

    if isinstance(value, BaseModel):
        value = value.model_dump(mode="python")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return _datetime_string(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        return _float_string(value, config.float_decimal_places)
    if isinstance(value, dict):
        return {
            str(key): canonical_value(item, config, parent_key=str(key))
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple)):
        normalized = [canonical_value(item, config) for item in value]
        identity_key = _SEMANTIC_LIST_KEYS.get(parent_key or "")
        if identity_key and all(
            isinstance(item, dict) and identity_key in item for item in normalized
        ):
            normalized.sort(key=lambda item: str(item[identity_key]))
        elif parent_key in _SEMANTIC_SORTED_LIST_KEYS:
            normalized.sort(
                key=lambda item: json.dumps(
                    item,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
        return normalized
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"unsupported canonical evidence value: {type(value).__name__}")


def canonical_json(value: Any, config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG) -> str:
    """Return canonical UTF-8 JSON text with stable keys and normalized values."""

    normalized = canonical_value(value, config)
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any, config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG) -> str:
    """Return a SHA-256 digest of canonical semantic content."""

    return hashlib.sha256(canonical_json(value, config).encode("utf-8")).hexdigest()


def hash_snapshot(snapshot: Any, config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG) -> str:
    return stable_hash(snapshot, config)


def hash_counterfactual(
    counterfactual: Any,
    config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG,
) -> str:
    return stable_hash(counterfactual, config)


def hash_config(tactical_config: Any, config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG) -> str:
    return stable_hash(tactical_config, config)


def hash_triangle(triangle: Any, config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG) -> str:
    return stable_hash(triangle, config)


def hash_analysis(analysis: Any, config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG) -> str:
    return stable_hash(analysis, config)


def hash_interaction(interaction: Any, config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG) -> str:
    return stable_hash(interaction, config)


def hash_route_opportunity(route: Any, config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG) -> str:
    return stable_hash(route, config)


def hash_claim_evidence(claim: Any, config: EvidenceConfig = DEFAULT_EVIDENCE_CONFIG) -> str:
    """Hash claim semantics while excluding mutable verification/lifecycle fields."""

    if isinstance(claim, BaseModel):
        payload = claim.model_dump(mode="python")
    elif isinstance(claim, dict):
        payload = claim
    else:
        payload = claim
    return stable_hash(_without_nonsemantic_claim_metadata(payload), config)


def _without_nonsemantic_claim_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_nonsemantic_claim_metadata(item)
            for key, item in value.items()
            if key not in _NONSEMANTIC_CLAIM_KEYS
        }
    if isinstance(value, (list, tuple)):
        return [_without_nonsemantic_claim_metadata(item) for item in value]
    return value
