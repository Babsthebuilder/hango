from fastapi.testclient import TestClient

from app.main import app
from app.models import SyntheticFixture, Team

client = TestClient(app)


def test_fixture_endpoints_list_and_load_validated_fixture() -> None:
    listing = client.get("/api/fixtures")
    fixture = client.get("/api/fixtures/positive-interaction")

    assert listing.status_code == 200
    assert listing.json() == ["blocked-triangle", "neutral-interaction", "positive-interaction"]
    assert fixture.status_code == 200
    assert fixture.json()["snapshot"]["snapshot_id"] == "positive-001-baseline"


def test_unknown_fixture_returns_404() -> None:
    assert client.get("/api/fixtures/not-present").status_code == 404


def test_analyze_endpoint_returns_typed_engine_output(
    positive_fixture: SyntheticFixture,
) -> None:
    response = client.post(
        "/api/tactical/analyze",
        json={
            "snapshot": positive_fixture.snapshot.model_dump(mode="json"),
            "ball_carrier_id": "H10",
            "attacking_team": Team.HOME,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["model_version"] == "tactical-v0.1"
    assert body["detected_triangles"]


def test_interaction_endpoint_returns_all_four_states(
    positive_fixture: SyntheticFixture,
) -> None:
    response = client.post(
        "/api/tactical/interaction",
        json={
            "snapshot": positive_fixture.snapshot.model_dump(mode="json"),
            "counterfactual": positive_fixture.counterfactual.model_dump(mode="json"),
            "ball_carrier_id": "H10",
            "support_b_id": "H07",
            "support_c_id": "H08",
            "attacking_team": Team.HOME,
        },
    )

    assert response.status_code == 200
    assert set(response.json()) >= {"u_00", "u_10", "u_01", "u_11", "interaction_value", "sign"}
