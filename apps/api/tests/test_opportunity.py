import pytest

from app.models import AttackingDirection, Position
from app.tactical.opportunity import evaluate_route, progression_value, state_opportunity
from app.tactical.schemas import PassingEdge


def _edge(accessibility: float, progression: float, pressure: float = 0.0) -> PassingEdge:
    return PassingEdge(
        origin_id="A",
        target_id="B",
        distance_m=10,
        lane_accessibility=accessibility,
        progression_value=progression,
        pressure_at_target=pressure,
    )


def test_advanced_route_scores_above_backward_route() -> None:
    forward = evaluate_route(("A", "B"), (_edge(1.0, 0.2),))
    backward = evaluate_route(("A", "B"), (_edge(1.0, -0.2),))

    assert forward.score > backward.score


def test_blocked_high_value_route_does_not_dominate_clear_moderate_route() -> None:
    blocked = evaluate_route(("A", "B"), (_edge(0.05, 0.8),))
    clear = evaluate_route(("A", "B"), (_edge(1.0, 0.2),))

    assert clear.score > blocked.score
    assert state_opportunity((blocked, clear)) == clear.score


def test_identical_routes_produce_identical_opportunity() -> None:
    first = evaluate_route(("A", "B"), (_edge(0.8, 0.2, 0.5),))
    second = evaluate_route(("A", "B"), (_edge(0.8, 0.2, 0.5),))

    assert first == second
    assert state_opportunity((first,)) == pytest.approx(state_opportunity((second,)))


def test_linear_pitch_value_respects_attacking_direction() -> None:
    origin = Position(x=40, y=20)
    target = Position(x=60, y=20)

    assert progression_value(origin, target, AttackingDirection.POSITIVE_X) > 0
    assert progression_value(origin, target, AttackingDirection.NEGATIVE_X) < 0
