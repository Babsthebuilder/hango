from app.models import Position, SyntheticFixture, Team
from app.tactical.config import TacticalConfig
from app.tactical.triangle_detector import build_triangle_candidate, detect_triangles


def _move_players(fixture: SyntheticFixture, positions: dict[str, Position]):
    players = tuple(
        player.model_copy(update={"position": positions[player.player_id]})
        if player.player_id in positions
        else player
        for player in fixture.snapshot.players
    )
    return fixture.snapshot.model_copy(update={"players": players})


def test_detector_returns_deterministic_same_team_candidates(
    positive_fixture: SyntheticFixture,
) -> None:
    first = detect_triangles(positive_fixture.snapshot, "H10", Team.HOME)
    second = detect_triangles(positive_fixture.snapshot, "H10", Team.HOME)

    assert first == second
    assert first
    assert all(candidate.player_ids[0] == "H10" for candidate in first)
    assert all(
        all(player_id.startswith("H") for player_id in candidate.player_ids)
        for candidate in first
    )


def test_detector_respects_support_radius(positive_fixture: SyntheticFixture) -> None:
    config = TacticalConfig(support_radius_m=5.0)

    assert detect_triangles(positive_fixture.snapshot, "H10", Team.HOME, config) == ()


def test_explicit_triangle_returns_structured_geometry(
    positive_fixture: SyntheticFixture,
) -> None:
    candidate = build_triangle_candidate(
        positive_fixture.snapshot,
        "H10",
        "H07",
        "H08",
        Team.HOME,
    )

    assert candidate.geometry.area_m2 > 0
    assert sum(
        (
            candidate.geometry.angles.carrier_degrees,
            candidate.geometry.angles.b_degrees,
            candidate.geometry.angles.c_degrees,
        )
    ) == 180.0
    assert 0 <= candidate.geometry.shape_quality <= 1


def test_near_degenerate_triangle_is_rejected_without_nan(
    positive_fixture: SyntheticFixture,
) -> None:
    snapshot = _move_players(
        positive_fixture,
        {
            "H07": Position(x=60.0, y=34.0),
            "H08": Position(x=61.0, y=34.0),
        },
    )

    candidate = build_triangle_candidate(snapshot, "H10", "H07", "H08", Team.HOME)

    assert not candidate.geometrically_valid
    assert candidate.rejection_reasons
    assert candidate.geometry.area_m2 == 0.0


def test_triangle_requires_attacking_teammates(positive_fixture: SyntheticFixture) -> None:
    try:
        build_triangle_candidate(
            positive_fixture.snapshot,
            "H10",
            "H07",
            "A08",
            Team.HOME,
        )
    except ValueError as error:
        assert "attacking team" in str(error)
    else:
        raise AssertionError("mixed-team triangle was accepted")
