import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

import { listFixtures, loadInvestigation } from "./api";
import { InvestigationWorkspace } from "./components/InvestigationWorkspace";
import type { InvestigationData } from "./types";
import "./styles.css";

export function App() {
  const [fixtureIds, setFixtureIds] = useState<string[]>([]);
  const [selectedFixture, setSelectedFixture] = useState("");
  const [data, setData] = useState<InvestigationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    listFixtures()
      .then((ids) => {
        if (cancelled) return;
        setFixtureIds(ids);
        const preferred = ids.includes("positive-interaction") ? "positive-interaction" : ids[0];
        setSelectedFixture(preferred ?? "");
        if (ids.length === 0) setLoading(false);
      })
      .catch((reason: unknown) => {
        if (cancelled) return;
        setError(reason instanceof Error ? reason.message : "Unable to load HANGO fixtures");
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  useEffect(() => {
    if (!selectedFixture) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    setData(null);
    loadInvestigation(selectedFixture)
      .then((investigation) => {
        if (!cancelled) setData(investigation);
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : "Unable to load investigation");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedFixture, reloadKey]);

  if (error) {
    return <ErrorState message={error} onRetry={() => setReloadKey((key) => key + 1)} />;
  }
  if (loading) {
    return <LoadingState />;
  }
  if (!data || fixtureIds.length === 0) {
    return <EmptyState onRetry={() => setReloadKey((key) => key + 1)} />;
  }
  return (
    <InvestigationWorkspace
      key={selectedFixture}
      data={data}
      fixtureIds={fixtureIds}
      selectedFixture={selectedFixture}
      onFixtureChange={setSelectedFixture}
    />
  );
}

function LoadingState() {
  return (
    <main className="system-state loading-state" aria-busy="true" aria-live="polite">
      <div className="loading-brand">H</div>
      <p className="kicker">Preparing investigation</p>
      <h1>Tracing the tactical evidence chain.</h1>
      <div className="loading-line" aria-hidden="true">
        <span />
      </div>
      <p>Loading observed state, deterministic analysis, modeled pressure, and verification.</p>
    </main>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <main className="system-state error-state" role="alert">
      <span className="state-code">CONNECTION / INVALID</span>
      <h1>The investigation could not be assembled.</h1>
      <p>{message}</p>
      <p className="state-help">Start the HANGO API locally, then retry the evidence chain.</p>
      <button type="button" onClick={onRetry}>
        Retry investigation
      </button>
    </main>
  );
}

function EmptyState({ onRetry }: { onRetry: () => void }) {
  return (
    <main className="system-state empty-state">
      <span className="state-code">NO MOMENTS</span>
      <h1>No validated investigation fixtures are available.</h1>
      <p>HANGO will not fabricate a football state or tactical result.</p>
      <button type="button" onClick={onRetry}>
        Check again
      </button>
    </main>
  );
}

const root = document.getElementById("root");
if (!root) {
  throw new Error("HANGO root element was not found");
}

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
