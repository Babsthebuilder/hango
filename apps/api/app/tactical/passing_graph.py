"""Directed attacking-team passing graph."""

from __future__ import annotations

from app.models import Snapshot, Team
from app.tactical.config import DEFAULT_TACTICAL_CONFIG, TacticalConfig
from app.tactical.gaussian_field import pressure_at_point
from app.tactical.opportunity import progression_value
from app.tactical.pass_lanes import analyze_passing_lane
from app.tactical.schemas import PassingEdge, PassingGraph


def build_passing_graph(
    snapshot: Snapshot,
    attacking_team: Team,
    config: TacticalConfig = DEFAULT_TACTICAL_CONFIG,
) -> PassingGraph:
    """Build deterministic directed edges above the accessibility threshold."""

    direction = snapshot.attacking_directions[attacking_team]
    attackers = sorted(
        (player for player in snapshot.players if player.team == attacking_team),
        key=lambda player: player.player_id,
    )
    defenders = tuple(player for player in snapshot.players if player.team != attacking_team)
    edges: list[PassingEdge] = []

    for origin in attackers:
        for target in attackers:
            if origin.player_id == target.player_id:
                continue
            if origin.position == target.position:
                continue
            lane = analyze_passing_lane(origin, target, defenders, config)
            if lane.accessibility < config.minimum_edge_accessibility:
                continue
            pressure = pressure_at_point(
                (target.position.x, target.position.y),
                defenders,
                config,
            )
            edges.append(
                PassingEdge(
                    origin_id=origin.player_id,
                    target_id=target.player_id,
                    distance_m=lane.distance_m,
                    lane_accessibility=lane.accessibility,
                    progression_value=progression_value(
                        origin.position,
                        target.position,
                        direction,
                    ),
                    pressure_at_target=pressure,
                )
            )

    return PassingGraph(
        snapshot_id=snapshot.snapshot_id,
        attacking_team=attacking_team,
        node_ids=tuple(player.player_id for player in attackers),
        edges=tuple(sorted(edges, key=lambda edge: (edge.origin_id, edge.target_id))),
    )


def edge_lookup(graph: PassingGraph) -> dict[tuple[str, str], PassingEdge]:
    """Index graph edges by directed endpoint pair."""

    return {(edge.origin_id, edge.target_id): edge for edge in graph.edges}


def usable_third_man_paths(
    graph: PassingGraph,
    carrier_id: str,
    support_b_id: str,
    support_c_id: str,
) -> tuple[tuple[str, str, str], ...]:
    """Return A->B->C and A->C->B only when both directed legs exist."""

    lookup = edge_lookup(graph)
    candidates = (
        (carrier_id, support_b_id, support_c_id),
        (carrier_id, support_c_id, support_b_id),
    )
    return tuple(
        path
        for path in candidates
        if (path[0], path[1]) in lookup and (path[1], path[2]) in lookup
    )
