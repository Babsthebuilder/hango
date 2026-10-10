import type { SyntheticFixture } from "../types";

interface WorkspaceHeaderProps {
  fixture: SyntheticFixture;
  fixtureIds: string[];
  selectedFixture: string;
  onFixtureChange: (fixtureId: string) => void;
  onOpenEvidence: () => void;
}

export function WorkspaceHeader({
  fixture,
  fixtureIds,
  selectedFixture,
  onFixtureChange,
  onOpenEvidence,
}: WorkspaceHeaderProps) {
  return (
    <header className="workspace-header">
      <div className="brand-lockup">
        <span className="brand-mark" aria-hidden="true">
          H
        </span>
        <div>
          <p className="kicker">Relational intelligence</p>
          <p className="brand-name">HANGO</p>
        </div>
      </div>

      <div className="moment-heading">
        <p className="kicker">Investigation 04 / synthetic laboratory</p>
        <h1>Reveal the support behind the route.</h1>
        <p>{fixture.description}</p>
      </div>

      <div className="header-actions">
        <label className="fixture-picker">
          <span>Scenario</span>
          <select
            value={selectedFixture}
            onChange={(event) => onFixtureChange(event.target.value)}
          >
            {fixtureIds.map((fixtureId) => (
              <option key={fixtureId} value={fixtureId}>
                {fixtureId.replaceAll("-", " ")}
              </option>
            ))}
          </select>
        </label>
        <button className="evidence-button" type="button" onClick={onOpenEvidence}>
          <EvidenceIcon />
          Inspect evidence
        </button>
      </div>
    </header>
  );
}

function EvidenceIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true">
      <path d="M10 2.25 16.5 5v4.75c0 3.8-2.65 6.65-6.5 8-3.85-1.35-6.5-4.2-6.5-8V5L10 2.25Z" />
      <path d="m7 10 2 2 4-4" />
    </svg>
  );
}
