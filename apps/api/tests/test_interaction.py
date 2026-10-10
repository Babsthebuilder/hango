import pytest

from app.tactical.interaction import four_state_interaction


def _fake_opportunity(b_moved: bool, c_moved: bool, pair_effect: float) -> float:
    """Test-only stub; this is explicitly not HANGO's production opportunity engine."""

    return 10.0 + 2.0 * b_moved + 3.0 * c_moved + pair_effect * b_moved * c_moved


@pytest.mark.parametrize(
    ("pair_effect", "expected_sign"),
    [(4.0, 1), (0.0, 0), (-4.0, -1)],
)
def test_four_state_interaction_algebra(pair_effect: float, expected_sign: int) -> None:
    u_00 = _fake_opportunity(False, False, pair_effect)
    u_10 = _fake_opportunity(True, False, pair_effect)
    u_01 = _fake_opportunity(False, True, pair_effect)
    u_11 = _fake_opportunity(True, True, pair_effect)

    interaction = four_state_interaction(u_00, u_10, u_01, u_11)

    assert interaction == pytest.approx(pair_effect)
    assert (interaction > 0) - (interaction < 0) == expected_sign
