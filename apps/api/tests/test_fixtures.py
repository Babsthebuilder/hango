from pathlib import Path

import pytest

from app.fixtures import load_fixture
from app.models import Team

FIXTURE_DIRECTORY = Path(__file__).parents[3] / "data" / "fixtures"
FIXTURE_PATHS = tuple(sorted(FIXTURE_DIRECTORY.glob("*.json")))


@pytest.mark.parametrize("fixture_path", FIXTURE_PATHS, ids=lambda path: path.stem)
def test_fixture_has_complete_valid_teams(fixture_path: Path) -> None:
    fixture = load_fixture(fixture_path)
    home = [player for player in fixture.snapshot.players if player.team == Team.HOME]
    away = [player for player in fixture.snapshot.players if player.team == Team.AWAY]

    assert len(fixture.snapshot.players) == 22
    assert len(home) == 11
    assert len(away) == 11
    assert len({player.player_id for player in fixture.snapshot.players}) == 22


@pytest.mark.parametrize("fixture_path", FIXTURE_PATHS, ids=lambda path: path.stem)
def test_fixture_coordinates_and_hypothetical_overrides_are_valid(fixture_path: Path) -> None:
    fixture = load_fixture(fixture_path)
    known_ids = {player.player_id for player in fixture.snapshot.players}

    assert fixture.counterfactual.player_overrides
    assert set(fixture.counterfactual.player_overrides) <= known_ids
    assert fixture.counterfactual.baseline_snapshot_id == fixture.snapshot.snapshot_id


def test_all_three_required_fixture_files_exist() -> None:
    assert {path.name for path in FIXTURE_PATHS} == {
        "blocked-triangle.json",
        "neutral-interaction.json",
        "positive-interaction.json",
    }
