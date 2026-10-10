import { applyPlayerOverrides, indexPlayers, PITCH_WIDTH_METRES, toPitchPoint } from "../geometry";
import type {
  CounterfactualComparison,
  PlayerState,
  PressureGridResult,
  RouteOpportunity,
  SnapshotAnalysis,
  SyntheticFixture,
  TacticalTriangleAnalysis,
  ViewMode,
} from "../types";

interface PitchProps {
  fixture: SyntheticFixture;
  comparison: CounterfactualComparison;
  pressure: PressureGridResult | null;
  viewMode: ViewMode;
  layerStage: number;
  showPressure: boolean;
}

export function Pitch({
  fixture,
  comparison,
  pressure,
  viewMode,
  layerStage,
  showPressure,
}: PitchProps) {
  const actualPlayers = fixture.snapshot.players;
  const alternativePlayers = applyPlayerOverrides(
    actualPlayers,
    fixture.counterfactual.player_overrides,
  );
  const actualAnalysis = comparison.baseline;
  const alternativeAnalysis = comparison.alternative;
  const activeAnalysis = viewMode === "alternative" ? alternativeAnalysis : actualAnalysis;
  const activeTriangle = activeAnalysis.ranked_tactical_triangles[0] ?? null;

  return (
    <figure className="pitch-figure">
      <div className="pitch-frame">
        <svg
          className="pitch"
          viewBox="-2 -2 109 72"
          role="img"
          aria-labelledby="pitch-title pitch-description"
          data-testid="tactical-pitch"
        >
          <title id="pitch-title">HANGO tactical investigation pitch</title>
          <desc id="pitch-description">
            A 105 by 68 metre football pitch showing actual and hypothetical player positions,
            tactical triangles, passing routes, and a modeled defensive pressure field.
          </desc>
          <defs>
            <linearGradient id="pitch-surface" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#123f31" />
              <stop offset="0.5" stopColor="#0f382b" />
              <stop offset="1" stopColor="#0a2b21" />
            </linearGradient>
            <pattern id="pitch-stripes" width="15" height="68" patternUnits="userSpaceOnUse">
              <rect width="7.5" height="68" fill="rgba(255,255,255,.018)" />
            </pattern>
            <filter id="player-shadow" x="-80%" y="-80%" width="260%" height="260%">
              <feDropShadow dx="0" dy="0.35" stdDeviation="0.45" floodOpacity="0.5" />
            </filter>
            <marker
              id="movement-arrow"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="4"
              markerHeight="4"
              orient="auto-start-reverse"
            >
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#ffd166" />
            </marker>
          </defs>

          <rect x="0" y="0" width="105" height="68" rx="0.7" fill="url(#pitch-surface)" />
          <rect x="0" y="0" width="105" height="68" rx="0.7" fill="url(#pitch-stripes)" />

          {showPressure && pressure ? <PressureLayer pressure={pressure} /> : null}

          <PitchMarkings />

          {viewMode === "compare" ? (
            <>
              <AnalysisLayers
                analysis={actualAnalysis}
                players={actualPlayers}
                stage={layerStage}
                variant="actual"
              />
              <AnalysisLayers
                analysis={alternativeAnalysis}
                players={alternativePlayers}
                stage={layerStage}
                variant="alternative"
              />
              <MovementVectors fixture={fixture} />
            </>
          ) : (
            <AnalysisLayers
              analysis={activeAnalysis}
              players={viewMode === "actual" ? actualPlayers : alternativePlayers}
              stage={layerStage}
              variant={viewMode}
            />
          )}

          {viewMode === "compare" ? (
            <>
              <PlayerLayer players={actualPlayers} variant="actual" />
              <AlternativePlayers fixture={fixture} players={alternativePlayers} />
            </>
          ) : (
            <PlayerLayer
              players={viewMode === "actual" ? actualPlayers : alternativePlayers}
              variant={viewMode}
            />
          )}

          <BallMarker position={fixture.snapshot.ball.position} />
          <DirectionMarker
            direction={fixture.snapshot.attacking_directions.HOME}
            team="HOME"
          />
          <DirectionMarker
            direction={fixture.snapshot.attacking_directions.AWAY}
            team="AWAY"
          />
        </svg>

        {layerStage > 0 && !activeTriangle && viewMode !== "compare" ? (
          <div className="pitch-empty" role="status">
            <span>No valid triangle at this reveal stage</span>
            Select another scenario or return to the observed state.
          </div>
        ) : null}
      </div>

      <figcaption className="pitch-caption">
        <span>
          <i className="legend-player legend-home" /> Home
        </span>
        <span>
          <i className="legend-player legend-away" /> Away
        </span>
        <span>
          <i className="legend-line legend-actual" /> Actual
        </span>
        <span>
          <i className="legend-line legend-alternative" /> Alternative · dashed
        </span>
        <span className="pitch-scale">105 × 68 metres · deterministic coordinate map</span>
      </figcaption>
    </figure>
  );
}

function PitchMarkings() {
  return (
    <g className="pitch-markings" aria-hidden="true">
      <rect x="0.5" y="0.5" width="104" height="67" rx="0.35" />
      <line x1="52.5" y1="0.5" x2="52.5" y2="67.5" />
      <circle cx="52.5" cy="34" r="9.15" />
      <circle cx="52.5" cy="34" r="0.6" className="pitch-dot" />
      <rect x="0.5" y="13.84" width="16.5" height="40.32" />
      <rect x="88" y="13.84" width="16.5" height="40.32" />
      <rect x="0.5" y="24.84" width="5.5" height="18.32" />
      <rect x="99" y="24.84" width="5.5" height="18.32" />
      <circle cx="11" cy="34" r="0.45" className="pitch-dot" />
      <circle cx="94" cy="34" r="0.45" className="pitch-dot" />
      <path d="M 17 26.6 A 9.15 9.15 0 0 1 17 41.4" />
      <path d="M 88 26.6 A 9.15 9.15 0 0 0 88 41.4" />
    </g>
  );
}

function PressureLayer({ pressure }: { pressure: PressureGridResult }) {
  const { x_coordinates: xs, y_coordinates: ys, values } = pressure.grid;
  let maximum = 0.000001;
  for (const row of values) {
    for (const value of row) maximum = Math.max(maximum, value);
  }
  return (
    <g
      className="pressure-layer"
      data-testid="pressure-layer"
      aria-label="Modeled defensive pressure field"
    >
      {ys.slice(0, -1).flatMap((y, rowIndex) =>
        xs.slice(0, -1).map((x, columnIndex) => {
          const nextX = xs[columnIndex + 1];
          const nextY = ys[rowIndex + 1];
          const intensity = Math.min(values[rowIndex][columnIndex] / maximum, 1);
          return (
            <rect
              key={`${x}-${y}`}
              x={x}
              y={PITCH_WIDTH_METRES - nextY}
              width={nextX - x + 0.08}
              height={nextY - y + 0.08}
              fill="#ff6b4a"
              opacity={intensity * 0.52}
            />
          );
        }),
      )}
    </g>
  );
}

interface AnalysisLayersProps {
  analysis: SnapshotAnalysis;
  players: PlayerState[];
  stage: number;
  variant: "actual" | "alternative";
}

function AnalysisLayers({ analysis, players, stage, variant }: AnalysisLayersProps) {
  const triangle = analysis.ranked_tactical_triangles[0];
  if (!triangle || stage < 1) {
    return null;
  }
  const playerIndex = indexPlayers(players);
  const trianglePoints = pointsForIds(triangle.triangle.player_ids, playerIndex);
  return (
    <g className={`analysis-layer analysis-${variant}`} data-testid={`${variant}-analysis-layer`}>
      <polygon
        className="triangle-shape"
        points={trianglePoints.map((point) => `${point.x},${point.y}`).join(" ")}
        data-testid={`${variant}-triangle`}
      />
      {stage >= 2 ? (
        <g data-testid={`${variant}-direct-lanes`}>
          {triangle.direct_lanes.map((lane) => (
            <RouteLine
              key={`${variant}-${lane.origin_id}-${lane.target_id}`}
              playerIds={[lane.origin_id, lane.target_id]}
              playerIndex={playerIndex}
              className="direct-lane"
            />
          ))}
        </g>
      ) : null}
      {stage >= 3 ? (
        <g data-testid={`${variant}-routes`}>
          {triangle.routes.slice(0, 4).map((route) => (
            <RoutePath
              key={`${variant}-${route.route_id}`}
              route={route}
              playerIndex={playerIndex}
            />
          ))}
        </g>
      ) : null}
    </g>
  );
}

function RouteLine({
  playerIds,
  playerIndex,
  className,
}: {
  playerIds: string[];
  playerIndex: Map<string, PlayerState>;
  className: string;
}) {
  const points = pointsForIds(playerIds, playerIndex);
  if (points.length !== 2) return null;
  return (
    <line
      className={className}
      x1={points[0].x}
      y1={points[0].y}
      x2={points[1].x}
      y2={points[1].y}
    />
  );
}

function RoutePath({
  route,
  playerIndex,
}: {
  route: RouteOpportunity;
  playerIndex: Map<string, PlayerState>;
}) {
  const points = pointsForIds(route.player_ids, playerIndex);
  if (points.length !== route.player_ids.length) return null;
  return (
    <polyline
      className="route-path"
      points={points.map((point) => `${point.x},${point.y}`).join(" ")}
    />
  );
}

function PlayerLayer({
  players,
  variant,
}: {
  players: PlayerState[];
  variant: "actual" | "alternative";
}) {
  return (
    <g className={`player-layer player-layer-${variant}`}>
      {players.map((player) => (
        <PlayerMarker key={`${variant}-${player.player_id}`} player={player} variant={variant} />
      ))}
    </g>
  );
}

function AlternativePlayers({
  fixture,
  players,
}: {
  fixture: SyntheticFixture;
  players: PlayerState[];
}) {
  const movedIds = new Set(Object.keys(fixture.counterfactual.player_overrides));
  return (
    <g className="player-layer player-layer-alternative">
      {players
        .filter((player) => movedIds.has(player.player_id))
        .map((player) => (
          <PlayerMarker key={`alternative-${player.player_id}`} player={player} variant="alternative" />
        ))}
    </g>
  );
}

function PlayerMarker({
  player,
  variant,
}: {
  player: PlayerState;
  variant: "actual" | "alternative";
}) {
  const point = toPitchPoint(player.position);
  return (
    <g
      className={`player player-${player.team.toLowerCase()} player-${variant}`}
      transform={`translate(${point.x} ${point.y})`}
      data-player-id={player.player_id}
    >
      <title>{`${player.player_id}, ${player.team}, ${variant} position`}</title>
      <circle r="1.65" />
      <text y="0.05">{player.player_id.slice(1)}</text>
      <text className="player-label" y="3.35">
        {player.player_id}
        {variant === "alternative" ? "′" : ""}
      </text>
    </g>
  );
}

function MovementVectors({ fixture }: { fixture: SyntheticFixture }) {
  const playerIndex = indexPlayers(fixture.snapshot.players);
  return (
    <g className="movement-vectors" data-testid="movement-vectors">
      {Object.entries(fixture.counterfactual.player_overrides).map(([playerId, position]) => {
        const player = playerIndex.get(playerId);
        if (!player) return null;
        const start = toPitchPoint(player.position);
        const end = toPitchPoint(position);
        return (
          <line
            key={playerId}
            x1={start.x}
            y1={start.y}
            x2={end.x}
            y2={end.y}
            markerEnd="url(#movement-arrow)"
            data-testid="movement-vector"
          />
        );
      })}
    </g>
  );
}

function BallMarker({ position }: { position: { x: number; y: number } }) {
  const point = toPitchPoint(position);
  return (
    <g className="ball-marker" transform={`translate(${point.x} ${point.y})`}>
      <circle r="0.82" />
      <circle r="0.28" />
      <title>Observed ball position</title>
    </g>
  );
}

function DirectionMarker({
  direction,
  team,
}: {
  direction: "POSITIVE_X" | "NEGATIVE_X";
  team: string;
}) {
  const positive = direction === "POSITIVE_X";
  const lineY = team === "HOME" ? -0.75 : 68.75;
  const textY = team === "HOME" ? -0.4 : 70.65;
  const tipX = positive ? 34 : 17;
  return (
    <g className="direction-marker" aria-label={`${team} attacks ${positive ? "right" : "left"}`}>
      <text x="2" y={textY}>
        {team} ATTACK
      </text>
      <line
        x1={positive ? 17 : 34}
        y1={lineY}
        x2={tipX}
        y2={lineY}
      />
      <path
        d={`M ${tipX} ${lineY} l ${positive ? -2 : 2} -1.2 v 2.4 z`}
      />
    </g>
  );
}

function pointsForIds(
  playerIds: readonly string[],
  playerIndex: Map<string, PlayerState>,
) {
  return playerIds.flatMap((playerId) => {
    const player = playerIndex.get(playerId);
    return player ? [toPitchPoint(player.position)] : [];
  });
}
