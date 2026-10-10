import { lazy, Suspense, useCallback, useState } from "react";

import { replayCalculation } from "../api";
import type { InvestigationData, ReplayResult, ViewMode } from "../types";
import { InsightRail } from "./InsightRail";
import { ExplanationPanel } from "./ExplanationPanel";
import { InvestigationControls } from "./InvestigationControls";
import { Pitch } from "./Pitch";
import { StatusBadge } from "./StatusBadge";
import { WorkspaceHeader } from "./WorkspaceHeader";

const EvidenceDrawer = lazy(() =>
  import("./EvidenceDrawer").then((module) => ({ default: module.EvidenceDrawer })),
);

interface InvestigationWorkspaceProps {
  data: InvestigationData;
  fixtureIds: string[];
  selectedFixture: string;
  onFixtureChange: (fixtureId: string) => void;
}

export function InvestigationWorkspace({
  data,
  fixtureIds,
  selectedFixture,
  onFixtureChange,
}: InvestigationWorkspaceProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("actual");
  const [layerStage, setLayerStage] = useState(0);
  const [showPressure, setShowPressure] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [replay, setReplay] = useState<ReplayResult | null>(null);
  const [replayLoading, setReplayLoading] = useState(false);
  const [replayError, setReplayError] = useState<string | null>(null);
  const reference = data.calculation.artifact.reference;
  const pressure =
    viewMode === "alternative"
      ? data.pressure.alternative
      : data.pressure.baseline;

  const closeDrawer = useCallback(() => setDrawerOpen(false), []);

  const runReplay = useCallback(async () => {
    setReplayLoading(true);
    setReplayError(null);
    try {
      const result = await replayCalculation(reference.calculation_id);
      setReplay(result);
    } catch (error) {
      setReplayError(error instanceof Error ? error.message : "Replay request failed");
    } finally {
      setReplayLoading(false);
    }
  }, [reference.calculation_id]);

  return (
    <main className="workspace-shell">
      <WorkspaceHeader
        fixture={data.fixture}
        fixtureIds={fixtureIds}
        selectedFixture={selectedFixture}
        onFixtureChange={onFixtureChange}
        onOpenEvidence={() => setDrawerOpen(true)}
      />

      <div className="workspace-meta" aria-label="Investigation metadata">
        <div>
          <span>Moment</span>
          <strong>{data.fixture.snapshot.snapshot_id}</strong>
        </div>
        <div>
          <span>Model</span>
          <strong>{reference.model_version}</strong>
        </div>
        <div>
          <span>Evidence</span>
          <StatusBadge value={data.claim.record.evidence.verification_status} />
        </div>
        <p>
          <span className="live-dot" aria-hidden="true" /> Local deterministic engine
        </p>
      </div>

      <InvestigationControls
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        layerStage={layerStage}
        onLayerStageChange={setLayerStage}
        showPressure={showPressure}
        onShowPressureChange={setShowPressure}
      />

      <div className="investigation-stage">
        <Pitch
          fixture={data.fixture}
          comparison={data.comparison}
          pressure={pressure}
          viewMode={viewMode}
          layerStage={layerStage}
          showPressure={showPressure}
        />
        <InsightRail
          comparison={data.comparison}
          viewMode={viewMode}
          layerStage={layerStage}
          onOpenEvidence={() => setDrawerOpen(true)}
        />
      </div>

      <ExplanationPanel
        calculationId={reference.calculation_id}
        claimId={data.claim.record.evidence.claim_id}
        onOpenEvidence={() => setDrawerOpen(true)}
      />

      <footer className="workspace-footer">
        <p>
          HANGO separates observed state, deterministic calculation, model estimate, and
          interpretation.
        </p>
        <span>Investigation workspace · Phase 5</span>
      </footer>

      {drawerOpen ? (
        <Suspense fallback={<div className="drawer-loading" role="status">Opening evidence…</div>}>
          <EvidenceDrawer
            open
            calculation={data.calculation}
            claim={data.claim}
            replay={replay}
            replayLoading={replayLoading}
            replayError={replayError}
            onReplay={runReplay}
            onClose={closeDrawer}
          />
        </Suspense>
      ) : null}
    </main>
  );
}
