import numpy as np
import pytest

from app.models import PlayerState, Position, Team
from app.tactical.config import TacticalConfig
from app.tactical.gaussian_field import (
    pressure_along_lane,
    pressure_at_point,
    pressure_at_points,
    pressure_grid,
)


def _defender() -> PlayerState:
    return PlayerState(player_id="A1", team=Team.AWAY, position=Position(x=50, y=34))


def test_pressure_is_maximum_at_defender_and_decreases_with_distance() -> None:
    defender = _defender()
    at_defender = pressure_at_point((50, 34), (defender,))
    near = pressure_at_point((52, 34), (defender,))
    far = pressure_at_point((60, 34), (defender,))

    assert at_defender == pytest.approx(1.0)
    assert at_defender > near > far >= 0


def test_pressure_is_symmetric_around_defender() -> None:
    defender = _defender()

    assert pressure_at_point((47, 34), (defender,)) == pytest.approx(
        pressure_at_point((53, 34), (defender,))
    )


def test_vectorized_points_are_deterministic() -> None:
    points = np.asarray(((50.0, 34.0), (55.0, 34.0)))
    first = pressure_at_points(points, (_defender(),))
    second = pressure_at_points(points, (_defender(),))

    assert np.array_equal(first, second)


def test_pressure_grid_is_deterministic_and_covers_pitch() -> None:
    config = TacticalConfig(pressure_grid_step_m=10.0)
    first = pressure_grid((_defender(),), config)
    second = pressure_grid((_defender(),), config)

    assert first == second
    assert first.x_coordinates[0] == 0.0
    assert first.x_coordinates[-1] == 105.0
    assert first.y_coordinates[-1] == 68.0
    assert len(first.values) == len(first.y_coordinates)


def test_pressure_along_lane_exposes_origin_receiver_and_samples() -> None:
    samples = pressure_along_lane((40, 34), (60, 34), (_defender(),))

    assert len(samples.along_lane) == 9
    assert samples.at_origin == pytest.approx(samples.at_target)
    assert samples.maximum_along_lane == pytest.approx(1.0)
