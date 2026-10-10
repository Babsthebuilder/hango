import pytest

from app.models import PlayerState, Position, Team
from app.tactical.config import TacticalConfig
from app.tactical.pass_lanes import analyze_passing_lane


def _player(player_id: str, team: Team, x: float, y: float) -> PlayerState:
    return PlayerState(player_id=player_id, team=team, position=Position(x=x, y=y))


def test_clear_lane_scores_one() -> None:
    lane = analyze_passing_lane(
        _player("H1", Team.HOME, 0, 0),
        _player("H2", Team.HOME, 10, 0),
        (),
    )

    assert lane.accessibility == 1.0
    assert lane.minimum_clearance_m is None


def test_defender_on_segment_fully_blocks_lane() -> None:
    lane = analyze_passing_lane(
        _player("H1", Team.HOME, 0, 0),
        _player("H2", Team.HOME, 10, 0),
        (_player("A1", Team.AWAY, 5, 0),),
    )

    assert lane.accessibility == 0.0
    assert lane.corridor_intruder_ids == ("A1",)
    assert lane.nearest_relevant_defender_id == "A1"


def test_defender_near_corridor_edge_has_intermediate_score() -> None:
    config = TacticalConfig(lane_corridor_radius_m=2.0, lane_falloff_m=3.0)
    lane = analyze_passing_lane(
        _player("H1", Team.HOME, 0, 0),
        _player("H2", Team.HOME, 10, 0),
        (_player("A1", Team.AWAY, 5, 2),),
        config,
    )

    assert 0.0 < lane.accessibility < 1.0
    assert lane.corridor_intruder_ids == ("A1",)


@pytest.mark.parametrize("defender_x", [-2.0, 12.0])
def test_defender_outside_segment_does_not_reduce_lane(defender_x: float) -> None:
    # Shift the segment on-pitch while retaining a defender behind/beyond it.
    lane = analyze_passing_lane(
        _player("H1", Team.HOME, 10, 10),
        _player("H2", Team.HOME, 20, 10),
        (_player("A1", Team.AWAY, defender_x + 10, 10),),
    )

    expected = 1.0 if defender_x < 0 or defender_x > 10 else 0.0
    assert lane.accessibility == expected
