from fastapi.testclient import TestClient

from app.evidence.models import CalculationArtifact, ClaimEvidence
from app.explanations.analyst import GroundingPacket
from app.explanations.models import ExplanationSentence
from app.explanations.providers import ExplanationProvider
from app.main import app
from app.routes.explanations import service
from app.runtime import evidence_registry, explanation_registry

client = TestClient(app)


class ApiFailingProvider(ExplanationProvider):
    provider_id = "failing-api"
    provider_version = "failing-api-v1"

    def compose(self, packet: GroundingPacket) -> tuple[ExplanationSentence, ...]:
        raise RuntimeError("configured provider failed")


def setup_function() -> None:
    evidence_registry.clear()
    explanation_registry.clear()


def register_grounding(
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
    client.post("/api/evidence/verify", json={"claim_id": supported_claim.claim_id})


def test_generate_retrieve_verify_and_invalidate_explanation(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    register_grounding(evidence_artifact, supported_claim)
    request = {
        "request_id": "api-explanation-request",
        "calculation_ids": [evidence_artifact.reference.calculation_id],
        "claim_ids": [supported_claim.claim_id],
        "provider_id": "local-template-v0.1",
    }

    generated = client.post("/api/explanations/generate", json=request)
    assert generated.status_code == 200
    artifact = generated.json()["artifact"]
    explanation_id = artifact["explanation_id"]
    assert artifact["verification"]["status"] == "SUPPORTED"
    assert artifact["publication_state"] == "READY"

    retrieved = client.get(f"/api/explanations/{explanation_id}")
    verified = client.post(f"/api/explanations/{explanation_id}/verify")
    invalidated = client.post(
        f"/api/explanations/{explanation_id}/invalidate",
        json={"reason": "editorial correction required"},
    )

    assert retrieved.status_code == 200
    assert verified.status_code == 200
    assert invalidated.status_code == 200
    assert invalidated.json()["artifact"]["publication_state"] == "INVALIDATED"
    assert len(invalidated.json()["artifact"]["verification_history"]) == 2


def test_explanation_api_rejects_unknown_provider_and_missing_sources(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    register_grounding(evidence_artifact, supported_claim)
    unknown_provider = client.post(
        "/api/explanations/generate",
        json={
            "request_id": "unknown-provider",
            "calculation_ids": [evidence_artifact.reference.calculation_id],
            "claim_ids": [supported_claim.claim_id],
            "provider_id": "foundry-not-configured",
        },
    )
    missing_source = client.post(
        "/api/explanations/generate",
        json={
            "request_id": "missing-source",
            "calculation_ids": ["calc:missing:0123456789abcdef"],
            "claim_ids": ["missing-claim"],
        },
    )

    assert unknown_provider.status_code == 422
    assert missing_source.status_code == 404
    assert client.get("/api/explanations/explanation:missing").status_code == 404


def test_explanation_retrieval_refreshes_stale_upstream_evidence(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    register_grounding(evidence_artifact, supported_claim)
    generated = client.post(
        "/api/explanations/generate",
        json={
            "request_id": "stale-refresh",
            "calculation_ids": [evidence_artifact.reference.calculation_id],
            "claim_ids": [supported_claim.claim_id],
        },
    )
    explanation_id = generated.json()["artifact"]["explanation_id"]
    client.post(
        "/api/evidence/stale",
        json={
            "evidence_id": evidence_artifact.reference.calculation_id,
            "reason": "model superseded",
        },
    )

    refreshed = client.get(f"/api/explanations/{explanation_id}")

    assert refreshed.status_code == 200
    assert refreshed.json()["artifact"]["verification"]["status"] == "STALE"
    assert refreshed.json()["artifact"]["publication_state"] == "STALE"


def test_explanation_retrieval_surfaces_invalidated_upstream_evidence(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    register_grounding(evidence_artifact, supported_claim)
    generated = client.post(
        "/api/explanations/generate",
        json={
            "request_id": "invalidated-refresh",
            "calculation_ids": [evidence_artifact.reference.calculation_id],
            "claim_ids": [supported_claim.claim_id],
        },
    )
    explanation_id = generated.json()["artifact"]["explanation_id"]
    client.post(
        "/api/evidence/invalidate",
        json={
            "evidence_id": evidence_artifact.reference.calculation_id,
            "reason": "calculation defect",
        },
    )

    refreshed = client.get(f"/api/explanations/{explanation_id}")

    assert refreshed.status_code == 200
    assert refreshed.json()["artifact"]["verification"]["status"] == "REJECTED"
    assert refreshed.json()["artifact"]["validity_state"] == "INVALIDATED"
    assert refreshed.json()["artifact"]["publication_state"] == "INVALIDATED"


def test_explanation_api_surfaces_provider_failure_as_bad_gateway(
    evidence_artifact: CalculationArtifact,
    supported_claim: ClaimEvidence,
) -> None:
    register_grounding(evidence_artifact, supported_claim)
    service.providers["failing-api"] = ApiFailingProvider()
    try:
        response = client.post(
            "/api/explanations/generate",
            json={
                "request_id": "provider-failure",
                "calculation_ids": [evidence_artifact.reference.calculation_id],
                "claim_ids": [supported_claim.claim_id],
                "provider_id": "failing-api",
            },
        )
    finally:
        service.providers.pop("failing-api", None)

    assert response.status_code == 502
    assert "configured provider failed" in response.json()["detail"]
