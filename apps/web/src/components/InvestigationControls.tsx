import type { ViewMode } from "../types";

export const LAYER_STAGES = [
  { value: 0, short: "State", label: "Observed state" },
  { value: 1, short: "Shape", label: "Candidate geometry" },
  { value: 2, short: "Lanes", label: "Direct passing lanes" },
  { value: 3, short: "Routes", label: "Third-player routes" },
  { value: 4, short: "Score", label: "Tactical score components" },
] as const;

interface InvestigationControlsProps {
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  layerStage: number;
  onLayerStageChange: (stage: number) => void;
  showPressure: boolean;
  onShowPressureChange: (show: boolean) => void;
}

export function InvestigationControls({
  viewMode,
  onViewModeChange,
  layerStage,
  onLayerStageChange,
  showPressure,
  onShowPressureChange,
}: InvestigationControlsProps) {
  return (
    <section className="investigation-controls" aria-label="Investigation controls">
      <div className="view-switcher" role="group" aria-label="Football state">
        {(["actual", "alternative", "compare"] as const).map((mode) => (
          <button
            key={mode}
            type="button"
            aria-pressed={viewMode === mode}
            onClick={() => onViewModeChange(mode)}
          >
            <span className={`line-key line-key-${mode}`} aria-hidden="true" />
            {mode === "actual" ? "Actual" : mode === "alternative" ? "Alternative" : "Compare"}
          </button>
        ))}
      </div>

      <div className="layer-stepper" aria-label="Triangle reveal stage">
        {LAYER_STAGES.map((stage) => (
          <button
            key={stage.value}
            type="button"
            className={layerStage === stage.value ? "is-active" : ""}
            aria-pressed={layerStage === stage.value}
            aria-label={`${stage.value + 1}. ${stage.label}`}
            onClick={() => onLayerStageChange(stage.value)}
          >
            <span>{String(stage.value + 1).padStart(2, "0")}</span>
            {stage.short}
          </button>
        ))}
      </div>

      <label className="pressure-toggle">
        <input
          type="checkbox"
          checked={showPressure}
          onChange={(event) => onShowPressureChange(event.target.checked)}
        />
        <span className="toggle-track" aria-hidden="true">
          <span />
        </span>
        <span>
          Pressure field
          <small>MODEL ESTIMATE</small>
        </span>
      </label>
    </section>
  );
}
