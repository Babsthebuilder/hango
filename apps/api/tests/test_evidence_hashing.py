from datetime import UTC, datetime

from app.evidence.config import DEFAULT_EVIDENCE_CONFIG
from app.evidence.hashing import (
    canonical_json,
    hash_claim_evidence,
    hash_config,
    hash_snapshot,
    stable_hash,
)
from app.evidence.models import (
    CalculationArtifact,
    ClaimEvidence,
    VerificationStatus,
)
from app.models import SyntheticFixture
from app.tactical.config import DEFAULT_TACTICAL_CONFIG


def test_canonical_json_has_stable_keys_enums_floats_and_datetimes() -> None:
    value = {
        "z": 1.25,
        "when": datetime(2026, 10, 10, 12, 30, tzinfo=UTC),
        "a": {"number": -0.0},
    }

    serialized = canonical_json(value)

    assert serialized == (
        '{"a":{"number":"0.000000000"},'
        '"when":"2026-10-10T12:30:00.000000Z","z":"1.250000000"}'
    )
    assert canonical_json(value) == serialized


def test_semantically_identical_snapshot_player_order_hashes_identically(
    positive_fixture: SyntheticFixture,
) -> None:
    snapshot = positive_fixture.snapshot
    reordered = snapshot.model_copy(update={"players": tuple(reversed(snapshot.players))})

    assert hash_snapshot(snapshot) == hash_snapshot(reordered)


def test_changed_tactical_input_and_config_change_hashes(
    positive_fixture: SyntheticFixture,
) -> None:
    snapshot = positive_fixture.snapshot
    changed_ball = snapshot.model_copy(
        update={"ball": snapshot.ball.model_copy(update={"in_play": False})}
    )
    changed_config = DEFAULT_TACTICAL_CONFIG.model_copy(
        update={"configuration_version": "tactical-config-v0.2"}
    )

    assert hash_snapshot(snapshot) != hash_snapshot(changed_ball)
    assert hash_config(DEFAULT_TACTICAL_CONFIG) != hash_config(changed_config)


def test_nonsemantic_claim_verification_metadata_does_not_change_hash(
    supported_claim: ClaimEvidence,
) -> None:
    verified = supported_claim.model_copy(
        update={
            "verification_status": VerificationStatus.SUPPORTED,
            "verification_reason": "Verified after deterministic replay",
        }
    )

    assert hash_claim_evidence(supported_claim) == hash_claim_evidence(verified)


def test_calculation_ids_are_deterministic_and_version_sensitive(
    evidence_artifact: CalculationArtifact,
) -> None:
    identity = {
        "calculation_kind": evidence_artifact.reference.calculation_kind,
        "input_hash": evidence_artifact.reference.input_hash,
        "output_hash": evidence_artifact.reference.output_hash,
        "model_version": evidence_artifact.reference.model_version,
        "configuration_version": evidence_artifact.reference.configuration_version,
        "schema_version": evidence_artifact.reference.schema_version,
    }
    expected_suffix = stable_hash(identity)[: DEFAULT_EVIDENCE_CONFIG.calculation_id_hash_length]

    assert evidence_artifact.reference.calculation_id.endswith(expected_suffix)
    assert stable_hash({**identity, "model_version": "tactical-v0.2"}) != stable_hash(identity)
