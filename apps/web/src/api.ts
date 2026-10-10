import type {
  CalculationDetails,
  ClaimDetails,
  ClaimEvidence,
  CounterfactualComparison,
  ExplanationDetails,
  InvestigationData,
  PressureGridComparison,
  ReplayResult,
  SyntheticFixture,
  Team,
  VerificationResult,
} from "./types";

const DEFAULT_BALL_CARRIER_ID = "H10";
const DEFAULT_ATTACKING_TEAM: Team = "HOME";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // Preserve the HTTP status text when the response is not JSON.
    }
    throw new ApiError(detail || "HANGO API request failed", response.status);
  }
  return (await response.json()) as T;
}

export function listFixtures(): Promise<string[]> {
  return request<string[]>("/api/fixtures");
}

export function getFixture(fixtureId: string): Promise<SyntheticFixture> {
  return request<SyntheticFixture>(`/api/fixtures/${encodeURIComponent(fixtureId)}`);
}

function analysisPayload(fixture: SyntheticFixture) {
  return {
    snapshot: fixture.snapshot,
    ball_carrier_id: DEFAULT_BALL_CARRIER_ID,
    attacking_team: DEFAULT_ATTACKING_TEAM,
  };
}

export function compareFixture(
  fixture: SyntheticFixture,
): Promise<CounterfactualComparison> {
  return request<CounterfactualComparison>("/api/tactical/compare", {
    method: "POST",
    body: JSON.stringify({
      ...analysisPayload(fixture),
      counterfactual: fixture.counterfactual,
    }),
  });
}

export function getPressureGrid(
  fixture: SyntheticFixture,
): Promise<PressureGridComparison> {
  return request<PressureGridComparison>("/api/tactical/pressure-grid", {
    method: "POST",
    body: JSON.stringify({
      snapshot: fixture.snapshot,
      counterfactual: fixture.counterfactual,
      attacking_team: DEFAULT_ATTACKING_TEAM,
    }),
  });
}

export function registerSnapshotAnalysis(
  fixture: SyntheticFixture,
): Promise<CalculationDetails> {
  return request<CalculationDetails>("/api/evidence/calculations/snapshot-analysis", {
    method: "POST",
    body: JSON.stringify(analysisPayload(fixture)),
  });
}

export function replayCalculation(calculationId: string): Promise<ReplayResult> {
  return request<ReplayResult>("/api/evidence/replay", {
    method: "POST",
    body: JSON.stringify({ calculation_id: calculationId }),
  });
}

export function getCalculation(calculationId: string): Promise<CalculationDetails> {
  return request<CalculationDetails>(
    `/api/evidence/calculations/${encodeURIComponent(calculationId)}`,
  );
}

export function getClaim(claimId: string): Promise<ClaimDetails> {
  return request<ClaimDetails>(`/api/evidence/claims/${encodeURIComponent(claimId)}`);
}

export function generateExplanation(
  calculationId: string,
  claimId: string,
): Promise<ExplanationDetails> {
  return request<ExplanationDetails>("/api/explanations/generate", {
    method: "POST",
    body: JSON.stringify({
      request_id: `workspace-explanation-${calculationId}`,
      calculation_ids: [calculationId],
      claim_ids: [claimId],
      provider_id: "local-template-v0.1",
      audience: "editorial",
    }),
  });
}

export function getExplanation(explanationId: string): Promise<ExplanationDetails> {
  return request<ExplanationDetails>(
    `/api/explanations/${encodeURIComponent(explanationId)}`,
  );
}

export function verifyExplanation(explanationId: string): Promise<ExplanationDetails> {
  return request<ExplanationDetails>(
    `/api/explanations/${encodeURIComponent(explanationId)}/verify`,
    { method: "POST" },
  );
}

export function invalidateExplanation(
  explanationId: string,
  reason: string,
): Promise<ExplanationDetails> {
  return request<ExplanationDetails>(
    `/api/explanations/${encodeURIComponent(explanationId)}/invalidate`,
    { method: "POST", body: JSON.stringify({ reason }) },
  );
}

function claimForCalculation(calculation: CalculationDetails): ClaimEvidence {
  const reference = calculation.artifact.reference;
  const score = calculation.artifact.authoritative_output.opportunity_score;
  return {
    claim_id: `workspace-${reference.calculation_id}`,
    claim_text: `The modeled opportunity score is ${score.toFixed(6)}.`,
    claim_type: "MODEL_ESTIMATE",
    evidence_classification: "MODEL_ESTIMATE",
    evidence_references: reference.created_from,
    numerical_assertions: [
      {
        calculation_id: reference.calculation_id,
        field_path: "opportunity_score",
        value: score,
        unit: "score",
      },
    ],
    calculation_references: [reference],
    model_version: reference.model_version,
    verification_status: "STALE",
    verification_reason: "Not yet verified",
    created_from: [reference.calculation_id],
    validity_state: "VALID",
    schema_version: reference.schema_version,
  };
}

async function ensureVerifiedClaim(calculation: CalculationDetails): Promise<ClaimDetails> {
  const claim = claimForCalculation(calculation);
  try {
    await request<{ item_id: string; item_type: string }>("/api/evidence/register", {
      method: "POST",
      body: JSON.stringify({ claim }),
    });
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 409) {
      throw error;
    }
  }
  await request<VerificationResult>("/api/evidence/verify", {
    method: "POST",
    body: JSON.stringify({ claim_id: claim.claim_id }),
  });
  return getClaim(claim.claim_id);
}

export async function loadInvestigation(fixtureId: string): Promise<InvestigationData> {
  const fixture = await getFixture(fixtureId);
  const [comparison, pressure, initialCalculation] = await Promise.all([
    compareFixture(fixture),
    getPressureGrid(fixture),
    registerSnapshotAnalysis(fixture),
  ]);
  const claim = await ensureVerifiedClaim(initialCalculation);
  const calculation = await getCalculation(initialCalculation.artifact.reference.calculation_id);
  return { fixture, comparison, pressure, calculation, claim };
}
