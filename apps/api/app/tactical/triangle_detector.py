"""Deterministic support-triangle candidate generation."""

from __future__ import annotations

from hashlib import sha256
from itertools import combinations

from app.models import PlayerState, Snapshot, Team
from app.tactical.config import DEFAULT_TACTICAL_CONFIG, TacticalConfig
from app.tactical.geometry import Point, calculate_triangle_geometry
from app.tactical.schemas import TriangleCandidate, TriangleRejection


def _point(player: PlayerState) -> Point:
    return player.position.x, player.position.y


def _triangle_id(snapshot_id: str, player_ids: tuple[str, str, str]) -> str:
    payload = "|".join((snapshot_id, *player_ids)).encode()
    return f"tri-{sha256(payload).hexdigest()[:16]}"


def _player_index(snapshot: Snapshot) -> dict[str, PlayerState]:
    return {player.player_id: player for player in snapshot.players}


def build_triangle_candidate(
    snapshot: Snapshot,
    ball_carrier_id: str,
    support_b_id: str,
    support_c_id: str,
    attacking_team: Team,
    config: TacticalConfig = DEFAULT_TACTICAL_CONFIG,
) -> TriangleCandidate:
    """Build one structured triangle candidate, including rejection reasons."""

    players = _player_index(snapshot)
    requested = (ball_carrier_id, support_b_id, support_c_id)
    if len(set(requested)) != 3:
        raise ValueError("triangle player IDs must be distinct")
    missing = set(requested) - set(players)
    if missing:
        raise ValueError(f"unknown triangle players: {', '.join(sorted(missing))}")
    if any(players[player_id].team != attacking_team for player_id in requested):
        raise ValueError("triangle players must all belong to the attacking team")

    ordered_supports = tuple(sorted((support_b_id, support_c_id)))
    player_ids = (ball_carrier_id, ordered_supports[0], ordered_supports[1])
    carrier, support_b, support_c = (players[player_id] for player_id in player_ids)
    geometry = calculate_triangle_geometry(_point(carrier), _point(support_b), _point(support_c))

    reasons: list[TriangleRejection] = []
    if geometry.distances.b_to_c_m < config.minimum_support_separation_m:
        reasons.append(TriangleRejection.SUPPORT_PLAYERS_TOO_CLOSE)
    if geometry.area_m2 < config.minimum_triangle_area_m2:
        reasons.append(TriangleRejection.AREA_BELOW_MINIMUM)
    if min(
        geometry.angles.carrier_degrees,
        geometry.angles.b_degrees,
        geometry.angles.c_degrees,
    ) < config.minimum_triangle_angle_degrees:
        reasons.append(TriangleRejection.ANGLE_BELOW_MINIMUM)
    if geometry.shape_quality == 0.0:
        reasons.append(TriangleRejection.DEGENERATE_GEOMETRY)

    unique_reasons = tuple(dict.fromkeys(reasons))
    return TriangleCandidate(
        triangle_id=_triangle_id(snapshot.snapshot_id, player_ids),
        snapshot_id=snapshot.snapshot_id,
        player_ids=player_ids,
        geometry=geometry,
        geometrically_valid=not unique_reasons,
        rejection_reasons=unique_reasons,
    )


def detect_triangles(
    snapshot: Snapshot,
    ball_carrier_id: str,
    attacking_team: Team,
    config: TacticalConfig = DEFAULT_TACTICAL_CONFIG,
) -> tuple[TriangleCandidate, ...]:
    """Generate all same-team support pairs within the configured carrier radius."""

    players = _player_index(snapshot)
    carrier = players.get(ball_carrier_id)
    if carrier is None:
        raise ValueError(f"unknown ball carrier: {ball_carrier_id}")
    if carrier.team != attacking_team:
        raise ValueError("ball carrier must belong to the attacking team")

    carrier_point = _point(carrier)
    supports = sorted(
        (
            player
            for player in snapshot.players
            if player.team == attacking_team
            and player.player_id != ball_carrier_id
            and _distance_without_import_cycle(carrier_point, _point(player))
            <= config.support_radius_m
        ),
        key=lambda player: player.player_id,
    )
    return tuple(
        build_triangle_candidate(
            snapshot,
            ball_carrier_id,
            first.player_id,
            second.player_id,
            attacking_team,
            config,
        )
        for first, second in combinations(supports, 2)
    )


def _distance_without_import_cycle(first: Point, second: Point) -> float:
    # Local arithmetic keeps support filtering independent of structured calculation creation.
    return ((second[0] - first[0]) ** 2 + (second[1] - first[1]) ** 2) ** 0.5
