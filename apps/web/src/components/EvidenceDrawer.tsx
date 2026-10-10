import { useEffect, useRef } from "react";

import { StatusBadge } from "./StatusBadge";
import type { CalculationDetails, ClaimDetails, ReplayResult } from "../types";

interface EvidenceDrawerProps {
  open: boolean;
  calculation: CalculationDetails;
  claim: ClaimDetails;
  replay: ReplayResult | null;
  replayLoading: boolean;
  replayError: string | null;
  onReplay: () => void;
  onClose: () => void;
}

const EPISTEMIC_LABELS = ["OBSERVED", "CALCULATED", "MODEL_ESTIMATE", "INTERPRETATION"] as const;
const VERIFICATION_LABELS = ["SUPPORTED", "QUALIFIED", "REJECTED", "STALE"] as const;

export function EvidenceDrawer({
  open,
  calculation,
  claim,
  replay,
  replayLoading,
  replayError,
  onReplay,
  onClose,
}: EvidenceDrawerProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const reference = calculation.artifact.reference;
  const claimEvidence = claim.record.evidence;

  useEffect(() => {
    if (!open) return;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    closeButtonRef.current?.focus();
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
      if (event.key === "Tab") {
        const drawer = closeButtonRef.current?.closest("aside");
        const focusable = drawer?.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], select, input:not([disabled]), [tabindex]:not([tabindex="-1"])',
        );
        if (!focusable?.length) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      previouslyFocused?.focus();
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="drawer-layer">
      <button
        type="button"
        className="drawer-scrim"
        aria-label="Close evidence drawer"
        onClick={onClose}
      />
      <aside
        className="evidence-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="evidence-title"
      >
        <header className="drawer-header">
          <div>
            <p className="kicker">Trust chain</p>
            <h2 id="evidence-title">Evidence ledger</h2>
          </div>
          <button
            type="button"
            className="icon-button"
            onClick={onClose}
            ref={closeButtonRef}
            aria-label="Close evidence drawer"
          >
            <span aria-hidden="true">×</span>
          </button>
        </header>

        <section className="drawer-status" aria-labelledby="claim-status-title">
          <div className="section-title-row">
            <div>
              <p className="kicker">Publication check</p>
              <h3 id="claim-status-title">Claim verification</h3>
            </div>
            <StatusBadge value={claimEvidence.verification_status} />
          </div>
          <blockquote>{claimEvidence.claim_text}</blockquote>
          <p>{claimEvidence.verification_reason}</p>
          <div className="status-pair">
            <StatusBadge value={claimEvidence.evidence_classification} subtle />
            <StatusBadge value={claimEvidence.validity_state} subtle />
          </div>
        </section>

        <section aria-labelledby="artifact-title">
          <div className="section-title-row">
            <div>
              <p className="kicker">Authoritative artifact</p>
              <h3 id="artifact-title">Snapshot analysis</h3>
            </div>
            <StatusBadge value={reference.validity_state} />
          </div>
          <dl className="evidence-list">
            <EvidenceRow label="Calculation ID" value={reference.calculation_id} code />
            <EvidenceRow label="Input hash" value={reference.input_hash} code />
            <EvidenceRow label="Output hash" value={reference.output_hash} code />
            <EvidenceRow label="Model" value={reference.model_version} />
            <EvidenceRow label="Configuration" value={reference.configuration_version} />
            <EvidenceRow label="Evidence schema" value={reference.schema_version} />
            <EvidenceRow label="Snapshot" value={reference.snapshot_id} />
          </dl>
        </section>

        <section aria-labelledby="replay-title" className="replay-section">
          <div className="section-title-row">
            <div>
              <p className="kicker">Deterministic check</p>
              <h3 id="replay-title">Replay</h3>
            </div>
            {replay ? (
              <span className={replay.replay_success ? "replay-pass" : "replay-fail"}>
                {replay.replay_success ? "Matched" : "Mismatch"}
              </span>
            ) : null}
          </div>
          {replayError ? (
            <div className="inline-error" role="alert">
              <strong>Replay unavailable</strong>
              <span>{replayError}</span>
            </div>
          ) : null}
          {replay ? (
            <div className={replay.replay_success ? "replay-result is-pass" : "replay-result is-fail"}>
              <span aria-hidden="true">{replay.replay_success ? "✓" : "!"}</span>
              <div>
                <strong>{replay.replay_success ? "Authoritative output matched" : "Replay failed"}</strong>
                <p>{replay.explanation}</p>
              </div>
            </div>
          ) : (
            <p className="muted-copy">Run the original inputs through tactical-v0.1 again.</p>
          )}
          <button
            className="replay-button"
            type="button"
            onClick={onReplay}
            disabled={replayLoading}
          >
            {replayLoading ? "Replaying…" : replay ? "Replay again" : "Run deterministic replay"}
          </button>
        </section>

        <section aria-labelledby="provenance-title">
          <p className="kicker">Provenance</p>
          <h3 id="provenance-title">Dependency chain</h3>
          <ol className="dependency-chain">
            <li>
              <span>01</span>
              <div>
                <strong>Football snapshot</strong>
                <code>{reference.created_from[0]?.reference_id ?? "No source reference"}</code>
              </div>
            </li>
            <li>
              <span>02</span>
              <div>
                <strong>Deterministic calculation</strong>
                <code>{reference.calculation_id}</code>
              </div>
            </li>
            <li>
              <span>03</span>
              <div>
                <strong>Verified claim</strong>
                <code>{claim.record.record_id}</code>
              </div>
            </li>
          </ol>
        </section>

        <section className="taxonomy" aria-labelledby="taxonomy-title">
          <p className="kicker">Reading key</p>
          <h3 id="taxonomy-title">Evidence language</h3>
          <div>
            {EPISTEMIC_LABELS.map((label) => (
              <StatusBadge key={label} value={label} subtle />
            ))}
          </div>
          <p className="taxonomy-note">
            Observed state and deterministic calculation remain distinct from model estimates and
            interpretation.
          </p>
          <div>
            {VERIFICATION_LABELS.map((label) => (
              <StatusBadge key={label} value={label} subtle />
            ))}
          </div>
        </section>
      </aside>
    </div>
  );
}

function EvidenceRow({
  label,
  value,
  code = false,
}: {
  label: string;
  value: string;
  code?: boolean;
}) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{code ? <code>{value}</code> : value}</dd>
    </div>
  );
}
