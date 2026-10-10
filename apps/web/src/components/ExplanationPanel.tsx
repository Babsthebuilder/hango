import { useCallback, useEffect, useState } from "react";

import { generateExplanation } from "../api";
import type { ExplanationArtifact } from "../types";
import { StatusBadge } from "./StatusBadge";

interface ExplanationPanelProps {
  calculationId: string;
  claimId: string;
  onOpenEvidence: () => void;
}

export function ExplanationPanel({
  calculationId,
  claimId,
  onOpenEvidence,
}: ExplanationPanelProps) {
  const [artifact, setArtifact] = useState<ExplanationArtifact | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  const retry = useCallback(() => setAttempt((value) => value + 1), []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    generateExplanation(calculationId, claimId)
      .then((details) => {
        if (!cancelled) setArtifact(details.artifact);
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setArtifact(null);
          setError(
            reason instanceof Error ? reason.message : "Explanation provider unavailable",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [attempt, calculationId, claimId]);

  return (
    <section
      className="explanation-panel"
      aria-labelledby="explanation-title"
      aria-busy={loading}
      aria-live="polite"
    >
      <header className="explanation-header">
        <div>
          <p className="kicker">Grounded editorial reading</p>
          <h2 id="explanation-title">What the evidence allows us to say</h2>
        </div>
        <StatusBadge value="INTERPRETATION" />
      </header>

      {loading ? <ExplanationLoading /> : null}
      {!loading && error ? <ExplanationFailure error={error} onRetry={retry} /> : null}
      {!loading && !error && artifact ? (
        <ExplanationContent artifact={artifact} onOpenEvidence={onOpenEvidence} />
      ) : null}
      {!loading && !error && !artifact ? <ExplanationEmpty onRetry={retry} /> : null}
    </section>
  );
}

function ExplanationLoading() {
  return (
    <div className="explanation-loading" role="status">
      <span aria-hidden="true" />
      <p>Retrieving registered evidence and running editorial verification…</p>
    </div>
  );
}

function ExplanationFailure({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <div className="explanation-failure" role="alert">
      <div>
        <strong>Grounded explanation unavailable</strong>
        <p>{error}</p>
      </div>
      <button type="button" onClick={onRetry}>Retry explanation</button>
    </div>
  );
}

function ExplanationEmpty({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="explanation-empty" role="status">
      <p>No grounded explanation was returned. HANGO will not invent one.</p>
      <button type="button" onClick={onRetry}>Check evidence again</button>
    </div>
  );
}

function ExplanationContent({
  artifact,
  onOpenEvidence,
}: {
  artifact: ExplanationArtifact;
  onOpenEvidence: () => void;
}) {
  const blocked =
    artifact.validity_state !== "VALID" || !artifact.verification.publishable;
  return (
    <div className={`explanation-content ${blocked ? "is-blocked" : ""}`}>
      <div className="editorial-decision">
        <StatusBadge value={artifact.verification.status} />
        <span className={`publication-state publication-${artifact.publication_state.toLowerCase()}`}>
          {artifact.publication_state.replaceAll("_", " ")}
        </span>
        <p>{artifact.verification.reason}</p>
      </div>

      {blocked ? (
        <div className="editorial-warning" role="alert">
          This interpretation is not cleared for publication. Inspect its evidence before use.
        </div>
      ) : null}

      {artifact.draft.sentences.length ? (
        <ol className="explanation-sentences">
          {artifact.draft.sentences.map((sentence) => (
            <li key={sentence.sentence_id}>
              <p>{sentence.text}</p>
              <div className="sentence-citations" aria-label={`Evidence for ${sentence.sentence_id}`}>
                {sentence.citations.map((citation, index) => (
                  <button
                    type="button"
                    key={citation.citation_id}
                    onClick={onOpenEvidence}
                    aria-label={`Open evidence citation ${index + 1} for sentence ${sentence.sentence_id}`}
                  >
                    <span aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>
                    {citation.field_path ?? "verified claim"}
                  </button>
                ))}
              </div>
            </li>
          ))}
        </ol>
      ) : (
        <p className="explanation-no-sentences">No publishable sentences were generated.</p>
      )}

      <footer className="explanation-provenance">
        <span>{artifact.draft.provider_id}</span>
        <span>{artifact.explanation_id}</span>
        <strong>AI prose cannot approve itself</strong>
      </footer>
    </div>
  );
}
