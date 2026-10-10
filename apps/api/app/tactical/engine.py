"""High-level orchestration for deterministic tactical engine v0.1."""

from __future__ import annotations

from statistics import fmean

from app.models import CounterfactualState, PlayerState, Position, Snapshot, Team
from app.tactical.config import DEFAULT_TACTICAL_CONFIG, TacticalConfig
from app.tactical.gaussian_field import pressure_at_point
from app.tactical.interaction import build_interaction_result
from app.tactical.opportunity import evaluate_route, score_triangle, state_opportunity
from app.tactical.pass_lanes import analyze_passing_lane
from app.tactical.passing_graph import build_passing_graph, edge_lookup, usable_third_man_paths
from app.tactical.schemas import (
    CounterfactualComparison,
    InteractionResult,
    PassingGraph,
    PressureSummary,
    SnapshotAnalysis,
    TacticalTriangleAnalysis,
    TriangleCandidate,
)
from app.tactical.triangle_detector import build_triangle_candidate, detect_triangles


class TacticalEngine:
    """Coordinate geometry, pressure, graph, opportunity, and interaction modules."""

    def __init__(self, config: TacticalConfig = DEFAULT_TACTICAL_CONFIG) -> None:
        self.config = config

    def detect_triangles(
        self,
        snapshot: Snapshot,
        ball_carrier_id: str,
        attacking_team: Team,
    ) -> tuple[TriangleCandidate, ...]:
        return detect_triangles(snapshot, ball_carrier_id, attacking_team, self.config)

    def analyze_triangle(
        self,
        snapshot: Snapshot,
        ball_carrier_id: str,
        support_b_id: str,
        support_c_id: str,
        attacking_team: Team,
        graph: PassingGraph | None = None,
    ) -> TacticalTriangleAnalysis:
        """Analyze one carrier/support triangle using inspectable components."""

        players = _player_index(snapshot)
        triangle = build_triangle_candidate(
            snapshot,
            ball_carrier_id,
            support_b_id,
            support_c_id,
            attacking_team,
            self.config,
        )
        carrier_id, support_b_id, support_c_id = triangle.player_ids
        carrier = players[carrier_id]
        support_b = players[support_b_id]
        support_c = players[support_c_id]
        defenders = tuple(player for player in snapshot.players if player.team != attacking_team)
        direct_lanes = (
            analyze_passing_lane(carrier, support_b, defenders, self.config),
            analyze_passing_lane(carrier, support_c, defenders, self.config),
        )

        graph = graph or build_passing_graph(snapshot, attacking_team, self.config)
        lookup = edge_lookup(graph)
        route_ids: list[tuple[str, ...]] = []
        for target_id in (support_b_id, support_c_id):
            if (carrier_id, target_id) in lookup:
                route_ids.append((carrier_id, target_id))
        route_ids.extend(
            usable_third_man_paths(graph, carrier_id, support_b_id, support_c_id)
        )
        routes = tuple(
            evaluate_route(
                player_ids,
                tuple(
                    lookup[(player_ids[index], player_ids[index + 1])]
                    for index in range(len(player_ids) - 1)
                ),
                self.config,
            )
            for player_ids in route_ids
        )
        receiver_pressures = (
            pressure_at_point(_point(support_b), defenders, self.config),
            pressure_at_point(_point(support_c), defenders, self.config),
        )
        return score_triangle(
            triangle,
            direct_lanes,
            routes,
            receiver_pressures,
            self.config,
        )

    def analyze_snapshot(
        self,
        snapshot: Snapshot,
        ball_carrier_id: str,
        attacking_team: Team,
        interaction: InteractionResult | None = None,
    ) -> SnapshotAnalysis:
        """Return detected/ranked triangles, routes, pressure, and U(S)."""

        triangles = self.detect_triangles(snapshot, ball_carrier_id, attacking_team)
        graph = build_passing_graph(snapshot, attacking_team, self.config)
        analyses = tuple(
            self.analyze_triangle(
                snapshot,
                ball_carrier_id,
                triangle.player_ids[1],
                triangle.player_ids[2],
                attacking_team,
                graph,
            )
            for triangle in triangles
            if triangle.geometrically_valid
        )
        ranked = tuple(
            sorted(
                analyses,
                key=lambda analysis: (-analysis.heuristic_score, analysis.triangle.triangle_id),
            )
        )
        unique_routes = {
            route.route_id: route for analysis in ranked for route in analysis.routes
        }
        best_routes = tuple(
            sorted(unique_routes.values(), key=lambda route: (-route.score, route.route_id))[
                : self.config.max_reported_routes
            ]
        )
        defenders = tuple(player for player in snapshot.players if player.team != attacking_team)
        attackers = tuple(player for player in snapshot.players if player.team == attacking_team)
        player_pressures = tuple(
            pressure_at_point(_point(player), defenders, self.config) for player in attackers
        )
        carrier = _require_player(snapshot, ball_carrier_id, attacking_team)
        pressure_summary = PressureSummary(
            at_ball_carrier=pressure_at_point(_point(carrier), defenders, self.config),
            mean_attacking_player_pressure=fmean(player_pressures),
            maximum_attacking_player_pressure=max(player_pressures),
        )
        return SnapshotAnalysis(
            snapshot_id=snapshot.snapshot_id,
            ball_carrier_id=ball_carrier_id,
            attacking_team=attacking_team,
            detected_triangles=triangles,
            ranked_tactical_triangles=ranked,
            best_passing_routes=best_routes,
            pressure_summary=pressure_summary,
            opportunity_score=state_opportunity(best_routes),
            interaction=interaction,
            model_version=self.config.model_version,
            configuration_version=self.config.configuration_version,
        )

    def compare_counterfactual(
        self,
        snapshot: Snapshot,
        counterfactual: CounterfactualState,
        ball_carrier_id: str,
        attacking_team: Team,
    ) -> CounterfactualComparison:
        """Compare full baseline and alternative analyses without mutating either state."""

        counterfactual.validate_against(snapshot)
        alternative = _snapshot_with_overrides(
            snapshot,
            counterfactual.player_overrides,
            counterfactual.counterfactual_id,
        )
        baseline_result = self.analyze_snapshot(snapshot, ball_carrier_id, attacking_team)
        alternative_result = self.analyze_snapshot(alternative, ball_carrier_id, attacking_team)
        return CounterfactualComparison(
            baseline=baseline_result,
            alternative=alternative_result,
            opportunity_delta=(
                alternative_result.opportunity_score - baseline_result.opportunity_score
            ),
        )

    def compute_interaction(
        self,
        snapshot: Snapshot,
        counterfactual: CounterfactualState,
        ball_carrier_id: str,
        support_b_id: str,
        support_c_id: str,
        attacking_team: Team,
    ) -> InteractionResult:
        """Evaluate the same triangle opportunity function across all four states."""

        counterfactual.validate_against(snapshot)
        if support_b_id == support_c_id:
            raise ValueError("interaction support players must be distinct")
        required = {support_b_id, support_c_id}
        if not required <= set(counterfactual.player_overrides):
            raise ValueError("counterfactual must explicitly override both support players")

        states = (
            snapshot,
            _snapshot_with_overrides(
                snapshot,
                {support_b_id: counterfactual.player_overrides[support_b_id]},
                f"{counterfactual.counterfactual_id}-10",
            ),
            _snapshot_with_overrides(
                snapshot,
                {support_c_id: counterfactual.player_overrides[support_c_id]},
                f"{counterfactual.counterfactual_id}-01",
            ),
            _snapshot_with_overrides(
                snapshot,
                {
                    support_b_id: counterfactual.player_overrides[support_b_id],
                    support_c_id: counterfactual.player_overrides[support_c_id],
                },
                f"{counterfactual.counterfactual_id}-11",
            ),
        )
        utilities = tuple(
            state_opportunity(
                self.analyze_triangle(
                    state,
                    ball_carrier_id,
                    support_b_id,
                    support_c_id,
                    attacking_team,
                ).routes
            )
            for state in states
        )
        return build_interaction_result(*utilities, config=self.config)


def _player_index(snapshot: Snapshot) -> dict[str, PlayerState]:
    return {player.player_id: player for player in snapshot.players}


def _require_player(snapshot: Snapshot, player_id: str, team: Team) -> PlayerState:
    player = _player_index(snapshot).get(player_id)
    if player is None:
        raise ValueError(f"unknown player: {player_id}")
    if player.team != team:
        raise ValueError("player must belong to the requested team")
    return player


def _point(player: PlayerState) -> tuple[float, float]:
    return player.position.x, player.position.y


def _snapshot_with_overrides(
    snapshot: Snapshot,
    overrides: dict[str, Position],
    state_id: str,
) -> Snapshot:
    known_ids = {player.player_id for player in snapshot.players}
    missing = set(overrides) - known_ids
    if missing:
        raise ValueError(f"unknown override players: {', '.join(sorted(missing))}")
    players = tuple(
        player.model_copy(update={"position": overrides[player.player_id]})
        if player.player_id in overrides
        else player
        for player in snapshot.players
    )
    return snapshot.model_copy(
        update={
            "snapshot_id": f"{snapshot.snapshot_id}@{state_id}",
            "provenance": f"{snapshot.provenance}; hypothetical state {state_id}",
            "players": players,
        }
    )
