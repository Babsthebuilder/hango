from fastapi.testclient import TestClient

from app.evidence.models import CalculationArtifact, ClaimEvidence, VerificationStatus
from app.main import app
from app.models import SyntheticFixture
from app.routes.evidence import registry

client = TestClient(app)


def setup_function() -> None:
    registry.clear()


def test_evidence_api_register_retrieve_verify_and_replay(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    calculation_id = evidence_artifact.reference.calculation_id

    registered_calculation = client.post(
        "/api/evidence/register",
        json={"calculation": evidence_artifact.model_dump(mode="json")},
    )
    registered_claim = client.post(
        "/api/evidence/register",
        json={"claim": supported_claim.model_dump(mode="json")},
    )
    calculation = client.get(f"/api/evidence/calculations/{calculation_id}")
    verification = client.post(
        "/api/evidence/verify",
        json={"claim_id": supported_claim.claim_id},
    )
    replay = client.post(
        "/api/evidence/replay",
        json={"calculation_id": calculation_id},
    )
    claim = client.get(f"/api/evidence/claims/{supported_claim.claim_id}")

    assert registered_calculation.status_code == 200
    assert registered_claim.status_code == 200
    assert calculation.status_code == 200
    assert calculation.json()["artifact"]["reference"]["output_hash"]
    assert verification.status_code == 200
    assert verification.json()["status"] == VerificationStatus.SUPPORTED
    assert replay.status_code == 200
    assert replay.json()["replay_success"] is True
    assert claim.json()["record"]["verification_history"]


def test_evidence_api_stale_propagates_to_claim(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    client.post(
        "/api/evidence/register",
        json={"calculation": evidence_artifact.model_dump(mode="json")},
    )
    client.post(
        "/api/evidence/register",
        json={"claim": supported_claim.model_dump(mode="json")},
    )
    snapshot_reference = evidence_artifact.reference.created_from[0].reference_id

    stale = client.post(
        "/api/evidence/stale",
        json={"evidence_id": snapshot_reference, "reason": "snapshot superseded"},
    )
    verification = client.post(
        "/api/evidence/verify",
        json={"claim_id": supported_claim.claim_id},
    )

    assert stale.status_code == 200
    assert evidence_artifact.reference.calculation_id in stale.json()["affected_ids"]
    assert verification.json()["status"] == VerificationStatus.STALE


def test_evidence_api_invalidate_propagates_without_deleting_history(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    client.post(
        "/api/evidence/register",
        json={"calculation": evidence_artifact.model_dump(mode="json")},
    )
    client.post(
        "/api/evidence/register",
        json={"claim": supported_claim.model_dump(mode="json")},
    )

    invalidated = client.post(
        "/api/evidence/invalidate",
        json={
            "evidence_id": evidence_artifact.reference.calculation_id,
            "reason": "authoritative calculation defect",
        },
    )
    calculation = client.get(
        f"/api/evidence/calculations/{evidence_artifact.reference.calculation_id}"
    )
    claim = client.get(f"/api/evidence/claims/{supported_claim.claim_id}")

    assert invalidated.status_code == 200
    assert calculation.status_code == 200
    assert calculation.json()["artifact"]["reference"]["validity_state"] == "INVALIDATED"
    assert claim.status_code == 200
    assert claim.json()["record"]["evidence"]["verification_status"] == "REJECTED"


def test_evidence_api_returns_not_found_for_unknown_items() -> None:
    assert client.get("/api/evidence/calculations/missing").status_code == 404
    assert client.get("/api/evidence/claims/missing").status_code == 404
    assert client.post(
        "/api/evidence/replay",
        json={"calculation_id": "missing"},
    ).status_code == 404


def test_snapshot_analysis_registration_returns_replayable_evidence(
    positive_fixture: SyntheticFixture,
) -> None:
    response = client.post(
        "/api/evidence/calculations/snapshot-analysis",
        json={
            "snapshot": positive_fixture.snapshot.model_dump(mode="json"),
            "ball_carrier_id": "H10",
            "attacking_team": "HOME",
        },
    )

    assert response.status_code == 200
    body = response.json()
    reference = body["artifact"]["reference"]
    assert reference["calculation_id"].startswith("calc:snapshot-analysis:")
    assert reference["input_hash"]
    assert reference["output_hash"]
    replay = client.post(
        "/api/evidence/replay",
        json={"calculation_id": reference["calculation_id"]},
    )
    assert replay.status_code == 200
    assert replay.json()["replay_success"] is True
