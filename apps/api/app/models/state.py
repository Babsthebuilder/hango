"""Validated football-state contracts."""

from __future__ import annotations

from collections import Counter
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

PITCH_LENGTH_METRES = 105.0
PITCH_WIDTH_METRES = 68.0


class Team(StrEnum):
    """Stable side identifiers for a single snapshot."""

    HOME = "HOME"
    AWAY = "AWAY"


class AttackingDirection(StrEnum):
    """Direction of travel along the pitch-length axis."""

    POSITIVE_X = "POSITIVE_X"
    NEGATIVE_X = "NEGATIVE_X"


class FixtureClass(StrEnum):
    """Synthetic scenario intent, not a calculated outcome."""

    POSITIVE_RELATIONAL_INTERACTION = "positive_relational_interaction"
    BLOCKED_TRIANGLE = "blocked_triangle"
    NEUTRAL_INTERACTION = "neutral_interaction"


class Position(BaseModel):
    """A point on the standard 105 m by 68 m pitch."""

    model_config = ConfigDict(frozen=True)

    x: float = Field(ge=0.0, le=PITCH_LENGTH_METRES)
    y: float = Field(ge=0.0, le=PITCH_WIDTH_METRES)


class PlayerState(BaseModel):
    """Observed state for one player at a snapshot."""

    model_config = ConfigDict(frozen=True)

    player_id: str = Field(min_length=1)
    team: Team
    position: Position


class BallState(BaseModel):
    """Observed ball state at a snapshot."""

    model_config = ConfigDict(frozen=True)

    position: Position
    in_play: bool = True


class Snapshot(BaseModel):
    """Complete, immutable football state at one instant."""

    model_config = ConfigDict(frozen=True)

    schema_version: str = Field(min_length=1)
    snapshot_id: str = Field(min_length=1)
    provenance: str = Field(min_length=1)
    attacking_directions: dict[Team, AttackingDirection]
    players: tuple[PlayerState, ...]
    ball: BallState

    @model_validator(mode="after")
    def validate_complete_match_state(self) -> Snapshot:
        """Enforce complete teams, stable identity, and explicit directions."""

        if len(self.players) != 22:
            raise ValueError("snapshot must contain exactly 22 players")

        player_ids = [player.player_id for player in self.players]
        if len(player_ids) != len(set(player_ids)):
            raise ValueError("player IDs must be unique")

        counts = Counter(player.team for player in self.players)
        if counts != Counter({Team.HOME: 11, Team.AWAY: 11}):
            raise ValueError("snapshot must contain exactly 11 players per team")

        if set(self.attacking_directions) != {Team.HOME, Team.AWAY}:
            raise ValueError("attacking direction must be explicit for both teams")
        if self.attacking_directions[Team.HOME] == self.attacking_directions[Team.AWAY]:
            raise ValueError("teams must attack in opposite directions")
        return self


class CounterfactualState(BaseModel):
    """Player-position overrides relative to an immutable baseline snapshot."""

    model_config = ConfigDict(frozen=True)

    counterfactual_id: str = Field(min_length=1)
    baseline_snapshot_id: str = Field(min_length=1)
    provenance: str = Field(min_length=1)
    player_overrides: dict[str, Position]

    @model_validator(mode="after")
    def require_overrides(self) -> CounterfactualState:
        """Require at least one explicit hypothetical movement."""

        if not self.player_overrides:
            raise ValueError("counterfactual must contain at least one player override")
        if any(not player_id for player_id in self.player_overrides):
            raise ValueError("override player IDs must be non-empty")
        return self

    def validate_against(self, snapshot: Snapshot) -> None:
        """Validate references without mutating the baseline snapshot."""

        if self.baseline_snapshot_id != snapshot.snapshot_id:
            raise ValueError("counterfactual baseline does not match snapshot")
        known_ids = {player.player_id for player in snapshot.players}
        missing_ids = set(self.player_overrides) - known_ids
        if missing_ids:
            missing = ", ".join(sorted(missing_ids))
            raise ValueError(f"counterfactual references unknown players: {missing}")


class SyntheticFixture(BaseModel):
    """A validated baseline and hypothetical state for a named test scenario."""

    model_config = ConfigDict(frozen=True)

    fixture_class: FixtureClass
    description: str = Field(min_length=1)
    snapshot: Snapshot
    counterfactual: CounterfactualState

    @model_validator(mode="after")
    def validate_counterfactual_reference(self) -> SyntheticFixture:
        self.counterfactual.validate_against(self.snapshot)
        return self
