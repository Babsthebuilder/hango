import { LAYER_STAGES } from "./InvestigationControls";
import { StatusBadge } from "./StatusBadge";
import type { CounterfactualComparison, SnapshotAnalysis, ViewMode } from "../types";

interface InsightRailProps {
  comparison: CounterfactualComparison;
  viewMode: ViewMode;
  layerStage: number;
  onOpenEvidence: () => void;
}

const SCORE_LABELS = {
  geometry: "Geometry",
  direct_lane: "Direct lane",
  third_man: "Third player",
  progression: "Progression",
  receiver_pressure: "Pressure relief",
} as const;

export function InsightRail({
  comparison,
  viewMode,
  layerStage,
  onOpenEvidence,
}: InsightRailProps) {
  const active = viewMode === "alternative" ? comparison.alternative : comparison.baseline;
  const triangle = active.ranked_tactical_triangles[0] ?? null;
  const stage = LAYER_STAGES[layerStage];

  return (
    <aside className="insight-rail" aria-label="Tactical reading">
      <div className="rail-index" aria-hidden="true">
        {String(layerStage + 1).padStart(2, "0")}
      </div>
      <div className="rail-heading">
        <p className="kicker">Reveal stage</p>
        <h2>{stage.label}</h2>
        <p>{stageDescription(layerStage)}</p>
      </div>

      <section className="metric-callout" aria-labelledby="opportunity-title">
        <div>
          <p className="metric-label" id="opportunity-title">
            Modeled opportunity
          </p>
          <strong>{formatScore(active.opportunity_score)}</strong>
        </div>
        <StatusBadge value="MODEL_ESTIMATE" />
        <p>
          Provisional route opportunity score. This is not xT and does not represent goal
          probability.
        </p>
      </section>

      <ComparisonReadout comparison={comparison} viewMode={viewMode} />

      {triangle ? (
        <section className="triangle-readout" aria-labelledby="triangle-title">
          <div className="section-title-row">
            <div>
              <p className="kicker">Primary triangle</p>
              <h3 id="triangle-title">{triangle.triangle.player_ids.join(" · ")}</h3>
            </div>
            <span className={triangle.tactically_useful ? "useful" : "limited"}>
              {triangle.tactically_useful ? "Useful" : "Limited"}
            </span>
          </div>

          {layerStage >= 4 ? (
            <ScoreComponents analysis={active} />
          ) : (
            <dl className="compact-metrics">
              <div>
                <dt>Area</dt>
                <dd>{triangle.triangle.geometry.area_m2.toFixed(1)} m²</dd>
              </div>
              <div>
                <dt>Shape</dt>
                <dd>{triangle.triangle.geometry.shape_quality.toFixed(2)}</dd>
              </div>
              <div>
                <dt>Routes</dt>
                <dd>{triangle.routes.length}</dd>
              </div>
            </dl>
          )}
        </section>
      ) : (
        <section className="empty-readout" role="status">
          <p className="kicker">No valid candidate</p>
          <h3>This state has no ranked tactical triangle.</h3>
          <p>The observed state remains available without inventing a tactical conclusion.</p>
        </section>
      )}

      <section className="pressure-readout" aria-labelledby="pressure-title">
        <div className="section-title-row">
          <div>
            <p className="kicker">Defensive field</p>
            <h3 id="pressure-title">Modeled pressure</h3>
          </div>
          <StatusBadge value="MODEL_ESTIMATE" subtle />
        </div>
        <dl className="compact-metrics">
          <div>
            <dt>At carrier</dt>
            <dd>{active.pressure_summary.at_ball_carrier.toFixed(2)}</dd>
          </div>
          <div>
            <dt>Team mean</dt>
            <dd>{active.pressure_summary.mean_attacking_player_pressure.toFixed(2)}</dd>
          </div>
          <div>
            <dt>Team max</dt>
            <dd>{active.pressure_summary.maximum_attacking_player_pressure.toFixed(2)}</dd>
          </div>
        </dl>
      </section>

      <button className="rail-evidence-link" type="button" onClick={onOpenEvidence}>
        View source hashes and replay
        <span aria-hidden="true">↗</span>
      </button>
    </aside>
  );
}

function ComparisonReadout({
  comparison,
  viewMode,
}: {
  comparison: CounterfactualComparison;
  viewMode: ViewMode;
}) {
  return (
    <section className="comparison-readout" aria-label="Actual versus alternative comparison">
      <div className={viewMode === "actual" ? "is-current" : ""}>
        <span>Actual</span>
        <strong>{formatScore(comparison.baseline.opportunity_score)}</strong>
      </div>
      <span className="comparison-arrow" aria-hidden="true">
        →
      </span>
      <div className={viewMode === "alternative" ? "is-current" : ""}>
        <span>Alternative</span>
        <strong>{formatScore(comparison.alternative.opportunity_score)}</strong>
      </div>
      <p>
        <span>Modeled difference</span>
        <strong>{formatSigned(comparison.opportunity_delta)}</strong>
      </p>
    </section>
  );
}

function ScoreComponents({ analysis }: { analysis: SnapshotAnalysis }) {
  const triangle = analysis.ranked_tactical_triangles[0];
  if (!triangle) return null;
  return (
    <div className="score-components" data-testid="score-components">
      <div className="score-total">
        <span>Heuristic score</span>
        <strong>{triangle.heuristic_score.toFixed(3)}</strong>
      </div>
      {Object.entries(triangle.score_components).map(([key, value]) => (
        <div className="score-row" key={key}>
          <div>
            <span>{SCORE_LABELS[key as keyof typeof SCORE_LABELS]}</span>
            <strong>{value.toFixed(2)}</strong>
          </div>
          <span className="score-track" aria-hidden="true">
            <span style={{ width: `${Math.max(2, value * 100)}%` }} />
          </span>
        </div>
      ))}
      <p>Inspectable weighted heuristic · not a universal measure of football quality.</p>
    </div>
  );
}

function stageDescription(stage: number): string {
  return [
    "Begin with the football state before revealing any tactical interpretation.",
    "The highest-ranked valid support triangle is outlined from server-calculated geometry.",
    "Direct corridors reveal geometric accessibility, not pass-completion probability.",
    "Usable direct and third-player routes are layered without implying intent.",
    "The complete, inspectable heuristic is decomposed into its five model components.",
  ][stage];
}

function formatScore(value: number): string {
  return value.toFixed(3);
}

function formatSigned(value: number): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(3)}`;
}
