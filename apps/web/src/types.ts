export type Team = "HOME" | "AWAY";
export type AttackingDirection = "POSITIVE_X" | "NEGATIVE_X";
export type ViewMode = "actual" | "alternative" | "compare";
export type ClaimType = "OBSERVED" | "CALCULATED" | "MODEL_ESTIMATE" | "INTERPRETATION";
export type VerificationStatus = "SUPPORTED" | "QUALIFIED" | "REJECTED" | "STALE";
export type ValidityState = "VALID" | "STALE" | "INVALIDATED";
export type PublicationState = "DRAFT" | "READY" | "BLOCKED" | "STALE" | "INVALIDATED";

export interface Position {
  x: number;
  y: number;
}

export interface PlayerState {
  player_id: string;
  team: Team;
  position: Position;
}

export interface Snapshot {
  schema_version: string;
  snapshot_id: string;
  provenance: string;
  attacking_directions: Record<Team, AttackingDirection>;
  players: PlayerState[];
  ball: { position: Position; in_play: boolean };
}

export interface CounterfactualState {
  counterfactual_id: string;
  baseline_snapshot_id: string;
  provenance: string;
  player_overrides: Record<string, Position>;
}

export interface SyntheticFixture {
  fixture_class: string;
  description: string;
  snapshot: Snapshot;
  counterfactual: CounterfactualState;
}

export interface TriangleCandidate {
  triangle_id: string;
  snapshot_id: string;
  player_ids: [string, string, string];
  geometry: {
    distances: {
      carrier_to_b_m: number;
      carrier_to_c_m: number;
      b_to_c_m: number;
    };
    angles: { carrier_degrees: number; b_degrees: number; c_degrees: number };
    area_m2: number;
    shape_quality: number;
  };
  geometrically_valid: boolean;
  rejection_reasons: string[];
}

export interface LaneAccessibility {
  origin_id: string;
  target_id: string;
  distance_m: number;
  accessibility: number;
  nearest_relevant_defender_id: string | null;
  minimum_clearance_m: number | null;
  corridor_intruder_ids: string[];
}

export interface RouteOpportunity {
  route_id: string;
  player_ids: string[];
  components: {
    lane_accessibility: number;
    progression_value: number;
    turnover_risk: number;
    risk_penalty: number;
  };
  score: number;
}

export interface TacticalTriangleAnalysis {
  triangle: TriangleCandidate;
  direct_lanes: [LaneAccessibility, LaneAccessibility];
  routes: RouteOpportunity[];
  score_components: {
    geometry: number;
    direct_lane: number;
    third_man: number;
    progression: number;
    receiver_pressure: number;
  };
  heuristic_score: number;
  tactically_useful: boolean;
  model_version: string;
  configuration_version: string;
}

export interface SnapshotAnalysis {
  snapshot_id: string;
  ball_carrier_id: string;
  attacking_team: Team;
  detected_triangles: TriangleCandidate[];
  ranked_tactical_triangles: TacticalTriangleAnalysis[];
  best_passing_routes: RouteOpportunity[];
  pressure_summary: {
    at_ball_carrier: number;
    mean_attacking_player_pressure: number;
    maximum_attacking_player_pressure: number;
  };
  opportunity_score: number;
  model_version: string;
  configuration_version: string;
}

export interface CounterfactualComparison {
  baseline: SnapshotAnalysis;
  alternative: SnapshotAnalysis;
  opportunity_delta: number;
}

export interface PressureGrid {
  x_coordinates: number[];
  y_coordinates: number[];
  values: number[][];
}

export interface PressureGridResult {
  grid: PressureGrid;
  evidence_classification: "MODEL_ESTIMATE";
  model_version: string;
  configuration_version: string;
}

export interface PressureGridComparison {
  baseline: PressureGridResult;
  alternative: PressureGridResult | null;
}

export interface EvidenceReference {
  reference_id: string;
  evidence_kind: string;
  object_id: string;
  content_hash: string;
  snapshot_id: string | null;
  calculation_id: string | null;
  model_version: string | null;
  source_provenance: string;
  validity_state: ValidityState;
  schema_version: string;
}

export interface CalculationReference {
  calculation_id: string;
  calculation_kind: string;
  input_hash: string;
  output_hash: string;
  snapshot_id: string;
  model_version: string;
  configuration_version: string;
  schema_version: string;
  created_from: EvidenceReference[];
  validity_state: ValidityState;
}

export interface CalculationArtifact {
  reference: CalculationReference;
  input_payload: Record<string, unknown>;
  authoritative_output: SnapshotAnalysis;
  configuration_payload: Record<string, unknown>;
  numerical_units: Record<string, string>;
}

export interface CalculationDetails {
  artifact: CalculationArtifact;
  dependencies: string[];
  dependents: string[];
}

export interface NumericalAssertion {
  calculation_id: string;
  field_path: string;
  value: number;
  unit: string;
}

export interface ClaimEvidence {
  claim_id: string;
  claim_text: string;
  claim_type: ClaimType;
  evidence_classification: ClaimType;
  evidence_references: EvidenceReference[];
  numerical_assertions: NumericalAssertion[];
  calculation_references: CalculationReference[];
  model_version: string;
  verification_status: VerificationStatus;
  verification_reason: string;
  created_from: string[];
  validity_state: ValidityState;
  schema_version: string;
}

export interface VerificationResult {
  claim_id: string;
  status: VerificationStatus;
  reason: string;
  replay_results: ReplayResult[];
  checked_evidence_ids: string[];
  suggested_claim_text: string | null;
}

export interface ClaimDetails {
  record: {
    record_id: string;
    evidence: ClaimEvidence;
    verification_history: VerificationResult[];
    supersedes: string | null;
  };
  dependencies: string[];
  dependents: string[];
}

export interface ReplayResult {
  calculation_id: string;
  replay_success: boolean;
  expected_output_hash: string;
  actual_output_hash: string | null;
  numeric_differences: Array<{
    field_path: string;
    expected: number;
    actual: number;
    absolute_difference: number;
    within_tolerance: boolean;
  }>;
  version_match: boolean;
  configuration_match: boolean;
  stale_dependencies: string[];
  explanation: string;
}

export interface InvestigationData {
  fixture: SyntheticFixture;
  comparison: CounterfactualComparison;
  pressure: PressureGridComparison;
  calculation: CalculationDetails;
  claim: ClaimDetails;
}

export interface EvidenceCitation {
  citation_id: string;
  sentence_id: string;
  claim_id: string;
  calculation_id: string | null;
  field_path: string | null;
  unit: string | null;
  numeric_value: number | null;
}

export interface ExplanationSentence {
  sentence_id: string;
  text: string;
  citations: EvidenceCitation[];
}

export interface ExplanationRequest {
  request_id: string;
  calculation_ids: string[];
  claim_ids: string[];
  provider_id: string;
  audience: string;
  schema_version: string;
}

export interface ExplanationDraft {
  draft_id: string;
  request_id: string;
  sentences: ExplanationSentence[];
  evidence_classification: "INTERPRETATION";
  provider_id: string;
  provider_version: string;
  schema_version: string;
}

export interface EditorialVerificationResult {
  explanation_id: string;
  status: VerificationStatus;
  publishable: boolean;
  reason: string;
  checked_claim_ids: string[];
  checked_calculation_ids: string[];
  offending_sentence_ids: string[];
  schema_version: string;
}

export interface ExplanationArtifact {
  explanation_id: string;
  request: ExplanationRequest;
  draft: ExplanationDraft;
  verification: EditorialVerificationResult;
  verification_history: EditorialVerificationResult[];
  publication_state: PublicationState;
  validity_state: ValidityState;
  schema_version: string;
}

export interface ExplanationDetails {
  artifact: ExplanationArtifact;
}
