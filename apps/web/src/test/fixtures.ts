import type {
  CalculationDetails,
  ClaimDetails,
  ExplanationDetails,
  InvestigationData,
  PlayerState,
  PressureGridComparison,
  SnapshotAnalysis,
  SyntheticFixture,
  TacticalTriangleAnalysis,
} from "../types";

const homePlayers: PlayerState[] = Array.from({ length: 11 }, (_, index) => ({
  player_id: `H${String(index + 1).padStart(2, "0")}`,
  team: "HOME",
  position: { x: 12 + index * 5, y: 8 + (index % 5) * 12 },
}));

const awayPlayers: PlayerState[] = Array.from({ length: 11 }, (_, index) => ({
  player_id: `A${String(index + 1).padStart(2, "0")}`,
  team: "AWAY",
  position: { x: 92 - index * 4, y: 7 + (index % 6) * 10 },
}));

const players = [...homePlayers, ...awayPlayers].map((player) => {
  if (player.player_id === "H10") return { ...player, position: { x: 59, y: 34 } };
  if (player.player_id === "H07") return { ...player, position: { x: 50, y: 25 } };
  if (player.player_id === "H08") return { ...player, position: { x: 50, y: 43 } };
  return player;
});

const fixture: SyntheticFixture = {
  fixture_class: "positive_relational_interaction",
  description: "Two support players widen and advance around the observed ball carrier.",
  snapshot: {
    schema_version: "0.1",
    snapshot_id: "positive-001-baseline",
    provenance: "HANGO synthetic fixture",
    attacking_directions: { HOME: "POSITIVE_X", AWAY: "NEGATIVE_X" },
    players,
    ball: { position: { x: 59, y: 34 }, in_play: true },
  },
  counterfactual: {
    counterfactual_id: "positive-001-both-supporters",
    baseline_snapshot_id: "positive-001-baseline",
    provenance: "HANGO synthetic hypothetical",
    player_overrides: {
      H07: { x: 78, y: 26 },
      H08: { x: 82, y: 46 },
    },
  },
};

function triangle(snapshotId: string, alternative = false): TacticalTriangleAnalysis {
  return {
    triangle: {
      triangle_id: `${snapshotId}:H10-H07-H08`,
      snapshot_id: snapshotId,
      player_ids: ["H10", "H07", "H08"],
      geometry: {
        distances: { carrier_to_b_m: 12, carrier_to_c_m: 12, b_to_c_m: 18 },
        angles: { carrier_degrees: 82, b_degrees: 49, c_degrees: 49 },
        area_m2: alternative ? 180 : 81,
        shape_quality: alternative ? 0.86 : 0.72,
      },
      geometrically_valid: true,
      rejection_reasons: [],
    },
    direct_lanes: [
      {
        origin_id: "H10",
        target_id: "H07",
        distance_m: 12,
        accessibility: alternative ? 0.84 : 0.55,
        nearest_relevant_defender_id: "A10",
        minimum_clearance_m: 3.2,
        corridor_intruder_ids: [],
      },
      {
        origin_id: "H10",
        target_id: "H08",
        distance_m: 12,
        accessibility: alternative ? 0.78 : 0.48,
        nearest_relevant_defender_id: "A08",
        minimum_clearance_m: 2.8,
        corridor_intruder_ids: [],
      },
    ],
    routes: [
      {
        route_id: `${snapshotId}:H10-H07-H08`,
        player_ids: ["H10", "H07", "H08"],
        components: {
          lane_accessibility: alternative ? 0.66 : 0.39,
          progression_value: 0.2,
          turnover_risk: 0.25,
          risk_penalty: 0.0875,
        },
        score: alternative ? 0.19 : 0.04,
      },
    ],
    score_components: {
      geometry: alternative ? 0.86 : 0.72,
      direct_lane: alternative ? 0.84 : 0.55,
      third_man: alternative ? 0.66 : 0.39,
      progression: 0.2,
      receiver_pressure: alternative ? 0.76 : 0.44,
    },
    heuristic_score: alternative ? 0.71 : 0.47,
    tactically_useful: true,
    model_version: "tactical-v0.1",
    configuration_version: "tactical-config-v0.1",
  };
}

function analysis(snapshotId: string, alternative = false): SnapshotAnalysis {
  const ranked = triangle(snapshotId, alternative);
  return {
    snapshot_id: snapshotId,
    ball_carrier_id: "H10",
    attacking_team: "HOME",
    detected_triangles: [ranked.triangle],
    ranked_tactical_triangles: [ranked],
    best_passing_routes: ranked.routes,
    pressure_summary: {
      at_ball_carrier: alternative ? 0.32 : 0.64,
      mean_attacking_player_pressure: alternative ? 0.21 : 0.29,
      maximum_attacking_player_pressure: alternative ? 0.65 : 0.91,
    },
    opportunity_score: alternative ? 0.19 : 0.04,
    model_version: "tactical-v0.1",
    configuration_version: "tactical-config-v0.1",
  };
}

const baselineAnalysis = analysis(fixture.snapshot.snapshot_id);
const alternativeAnalysis = analysis(`${fixture.snapshot.snapshot_id}@alternative`, true);

const pressure: PressureGridComparison = {
  baseline: {
    grid: {
      x_coordinates: [0, 52.5, 105],
      y_coordinates: [0, 34, 68],
      values: [
        [0.1, 0.3, 0.1],
        [0.2, 1, 0.2],
        [0.1, 0.3, 0.1],
      ],
    },
    evidence_classification: "MODEL_ESTIMATE",
    model_version: "tactical-v0.1",
    configuration_version: "tactical-config-v0.1",
  },
  alternative: {
    grid: {
      x_coordinates: [0, 52.5, 105],
      y_coordinates: [0, 34, 68],
      values: [
        [0.1, 0.2, 0.1],
        [0.1, 0.7, 0.1],
        [0.1, 0.2, 0.1],
      ],
    },
    evidence_classification: "MODEL_ESTIMATE",
    model_version: "tactical-v0.1",
    configuration_version: "tactical-config-v0.1",
  },
};

const hash = "a".repeat(64);
const calculationId = "calc:snapshot-analysis:0123456789abcdefabcd";

const calculation: CalculationDetails = {
  artifact: {
    reference: {
      calculation_id: calculationId,
      calculation_kind: "SNAPSHOT_ANALYSIS",
      input_hash: hash,
      output_hash: "b".repeat(64),
      snapshot_id: fixture.snapshot.snapshot_id,
      model_version: "tactical-v0.1",
      configuration_version: "tactical-config-v0.1",
      schema_version: "evidence-schema-v0.1",
      created_from: [
        {
          reference_id: "snapshot:positive-001-baseline:0123456789abcdefabcd",
          evidence_kind: "SNAPSHOT",
          object_id: fixture.snapshot.snapshot_id,
          content_hash: "c".repeat(64),
          snapshot_id: fixture.snapshot.snapshot_id,
          calculation_id: null,
          model_version: null,
          source_provenance: fixture.snapshot.provenance,
          validity_state: "VALID",
          schema_version: "0.1",
        },
      ],
      validity_state: "VALID",
    },
    input_payload: {},
    authoritative_output: baselineAnalysis,
    configuration_payload: {},
    numerical_units: { opportunity_score: "score" },
  },
  dependencies: ["snapshot:positive-001-baseline:0123456789abcdefabcd"],
  dependents: ["workspace-claim"],
};

const claim: ClaimDetails = {
  record: {
    record_id: "claim-record:workspace-claim:0123456789abcdefabcd",
    evidence: {
      claim_id: "workspace-claim",
      claim_text: "The modeled opportunity score is 0.040000.",
      claim_type: "MODEL_ESTIMATE",
      evidence_classification: "MODEL_ESTIMATE",
      evidence_references: calculation.artifact.reference.created_from,
      numerical_assertions: [
        { calculation_id: calculationId, field_path: "opportunity_score", value: 0.04, unit: "score" },
      ],
      calculation_references: [calculation.artifact.reference],
      model_version: "tactical-v0.1",
      verification_status: "SUPPORTED",
      verification_reason: "Current deterministic evidence supports the claim",
      created_from: [calculationId],
      validity_state: "VALID",
      schema_version: "evidence-schema-v0.1",
    },
    verification_history: [],
    supersedes: null,
  },
  dependencies: [calculationId],
  dependents: [],
};

export function makeInvestigationData(): InvestigationData {
  return {
    fixture: structuredClone(fixture),
    comparison: {
      baseline: structuredClone(baselineAnalysis),
      alternative: structuredClone(alternativeAnalysis),
      opportunity_delta: 0.15,
    },
    pressure: structuredClone(pressure),
    calculation: structuredClone(calculation),
    claim: structuredClone(claim),
  };
}

export function makeExplanationDetails(
  status: "SUPPORTED" | "QUALIFIED" | "REJECTED" | "STALE" = "SUPPORTED",
): ExplanationDetails {
  const publishable = status === "SUPPORTED" || status === "QUALIFIED";
  const publicationState =
    status === "STALE" ? "STALE" : publishable ? "READY" : "BLOCKED";
  const verification = {
    explanation_id: "explanation:0123456789abcdefabcd",
    status,
    publishable,
    reason: publishable
      ? "Every sentence and numerical statement is grounded in current evidence"
      : "Referenced evidence is not cleared for publication",
    checked_claim_ids: [claim.record.evidence.claim_id],
    checked_calculation_ids: [calculationId],
    offending_sentence_ids: [],
    schema_version: "explanation-schema-v0.1",
  };
  return {
    artifact: {
      explanation_id: "explanation:0123456789abcdefabcd",
      request: {
        request_id: "workspace-explanation-request",
        calculation_ids: [calculationId],
        claim_ids: [claim.record.evidence.claim_id],
        provider_id: "local-template-v0.1",
        audience: "editorial",
        schema_version: "explanation-schema-v0.1",
      },
      draft: {
        draft_id: "draft:0123456789abcdefabcd",
        request_id: "workspace-explanation-request",
        evidence_classification: "INTERPRETATION",
        provider_id: "local-template-v0.1",
        provider_version: "local-template-v0.1",
        schema_version: "explanation-schema-v0.1",
        sentences: [
          {
            sentence_id: "sentence-01",
            text: "The modeled opportunity score is 0.040000.",
            citations: [
              {
                citation_id: "sentence-01-numeric-01",
                sentence_id: "sentence-01",
                claim_id: claim.record.evidence.claim_id,
                calculation_id: calculationId,
                field_path: "opportunity_score",
                unit: "score",
                numeric_value: 0.04,
              },
            ],
          },
        ],
      },
      verification,
      verification_history: [verification],
      publication_state: publicationState,
      validity_state: status === "STALE" ? "STALE" : "VALID",
      schema_version: "explanation-schema-v0.1",
    },
  };
}
