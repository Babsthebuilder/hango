import pytest

from app.models import SyntheticFixture, Team
from app.tactical.engine import TacticalEngine
from app.tactical.interaction import build_interaction_result
from app.tactical.schemas import InteractionSign


def test_blocked_triangle_is_penalized_against_opener_triangle(
    blocked_fixture: SyntheticFixture,
    positive_fixture: SyntheticFixture,
) -> None:
    engine = TacticalEngine()
    blocked = engine.analyze_triangle(
        blocked_fixture.snapshot,
        "H10",
        "H07",
        "H08",
        Team.HOME,
    )
    positive = engine.analyze_triangle(
        positive_fixture.snapshot,
        "H10",
        "H07",
        "H08",
        Team.HOME,
    )

    assert blocked.triangle.geometrically_valid
    assert blocked.heuristic_score < positive.heuristic_score
    assert not blocked.tactically_useful


def test_snapshot_analysis_is_deterministic(positive_fixture: SyntheticFixture) -> None:
    engine = TacticalEngine()

    first = engine.analyze_snapshot(positive_fixture.snapshot, "H10", Team.HOME)
    second = engine.analyze_snapshot(positive_fixture.snapshot, "H10", Team.HOME)

    assert first == second
    assert first.detected_triangles
    assert first.ranked_tactical_triangles
    assert first.model_version == "tactical-v0.1"


def test_counterfactual_comparison_preserves_baseline(
    positive_fixture: SyntheticFixture,
) -> None:
    engine = TacticalEngine()
    original = positive_fixture.snapshot.model_dump_json()

    comparison = engine.compare_counterfactual(
        positive_fixture.snapshot,
        positive_fixture.counterfactual,
        "H10",
        Team.HOME,
    )

    assert positive_fixture.snapshot.model_dump_json() == original
    assert comparison.baseline.snapshot_id == positive_fixture.snapshot.snapshot_id
    assert comparison.alternative.snapshot_id != comparison.baseline.snapshot_id


@pytest.mark.parametrize(
    ("utilities", "expected"),
    [
        ((0.0, 0.1, 0.1, 0.3), InteractionSign.POSITIVE),
        ((0.0, 0.1, 0.1, 0.2), InteractionSign.NEUTRAL),
        ((0.0, 0.2, 0.2, 0.3), InteractionSign.NEGATIVE),
    ],
)
def test_interaction_sign_classification(
    utilities: tuple[float, float, float, float],
    expected: InteractionSign,
) -> None:
    assert build_interaction_result(*utilities).sign == expected


def test_interaction_requires_both_explicit_overrides(
    positive_fixture: SyntheticFixture,
) -> None:
    incomplete = positive_fixture.counterfactual.model_copy(
        update={
            "player_overrides": {
                "H07": positive_fixture.counterfactual.player_overrides["H07"]
            }
        }
    )

    with pytest.raises(ValueError, match="both support players"):
        TacticalEngine().compute_interaction(
            positive_fixture.snapshot,
            incomplete,
            "H10",
            "H07",
            "H08",
            Team.HOME,
        )


def test_positive_fixture_produces_positive_modeled_interaction(
    positive_fixture: SyntheticFixture,
) -> None:
    result = TacticalEngine().compute_interaction(
        positive_fixture.snapshot,
        positive_fixture.counterfactual,
        "H10",
        "H07",
        "H08",
        Team.HOME,
    )

    assert result.sign == InteractionSign.POSITIVE
    assert result.u_11 > result.u_10
    assert result.u_11 > result.u_01


def test_neutral_fixture_is_approximately_additive(
    neutral_fixture: SyntheticFixture,
) -> None:
    result = TacticalEngine().compute_interaction(
        neutral_fixture.snapshot,
        neutral_fixture.counterfactual,
        "H10",
        "H07",
        "H08",
        Team.HOME,
    )

    assert result.sign == InteractionSign.NEUTRAL
    assert result.u_10 > result.u_00
    assert result.u_01 > result.u_00
