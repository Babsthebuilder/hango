from app.models import SyntheticFixture, Team
from app.tactical.engine import TacticalEngine
from app.tactical.passing_graph import build_passing_graph, edge_lookup, usable_third_man_paths
from app.tactical.schemas import PassingEdge, PassingGraph


def test_graph_contains_valid_directed_edges(positive_fixture: SyntheticFixture) -> None:
    graph = build_passing_graph(positive_fixture.snapshot, Team.HOME)
    lookup = edge_lookup(graph)

    assert len(graph.node_ids) == 11
    assert ("H10", "H07") in lookup
    assert lookup[("H10", "H07")].origin_id == "H10"
    assert 0.0 <= lookup[("H10", "H07")].lane_accessibility <= 1.0


def test_blocked_edge_is_omitted(blocked_fixture: SyntheticFixture) -> None:
    graph = build_passing_graph(blocked_fixture.snapshot, Team.HOME)

    assert ("H10", "H07") not in edge_lookup(graph)


def test_third_man_path_requires_both_directed_legs() -> None:
    first = PassingEdge(
        origin_id="A",
        target_id="B",
        distance_m=10,
        lane_accessibility=1,
        progression_value=0.1,
        pressure_at_target=0,
    )
    second = PassingEdge(
        origin_id="B",
        target_id="C",
        distance_m=10,
        lane_accessibility=1,
        progression_value=0.1,
        pressure_at_target=0,
    )
    graph = PassingGraph(
        snapshot_id="s",
        attacking_team=Team.HOME,
        node_ids=("A", "B", "C"),
        edges=(first, second),
    )

    assert usable_third_man_paths(graph, "A", "B", "C") == (("A", "B", "C"),)
    missing_leg = graph.model_copy(update={"edges": (first,)})
    assert usable_third_man_paths(missing_leg, "A", "B", "C") == ()


def test_engine_exposes_third_man_routes_when_usable(
    positive_fixture: SyntheticFixture,
) -> None:
    analysis = TacticalEngine().analyze_triangle(
        positive_fixture.snapshot,
        "H10",
        "H07",
        "H08",
        Team.HOME,
    )

    assert any(len(route.player_ids) == 3 for route in analysis.routes)
