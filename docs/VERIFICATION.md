# Verification

HANGO separates computation from publication approval.

## Publication statuses

- `SUPPORTED`: all factual assertions resolve to current deterministic evidence.
- `QUALIFIED`: the evidence supports a narrower statement or the claim is explicitly interpretive.
- `REJECTED`: evidence is missing, contradictory, or an unsupported intent/causal claim is asserted.
- `STALE`: a referenced input, calculation, or model version has been superseded or invalidated.

## Required checks

Before publication, a verifier must confirm that referenced events, snapshots, calculations, and model versions exist; recompute or hash-check deterministic numerical values; and ensure claim classifications match the evidence type. Every factual number must trace to deterministic evidence.

Generated prose cannot approve itself. Unsupported tactical intent and causal language must be rejected or qualified. A correction creates a new evidence record or version and marks dependent prior claims stale; records are not silently rewritten.

## Phase 2 automation

`scripts/verify.sh` validates all JSON fixtures, runs Ruff over API and benchmark code, executes Pytest, and type-checks/builds the unchanged frontend. CI calls the same script.

The tactical suite verifies rigid-geometry invariants, degenerate rejection, continuous lane behavior, Gaussian symmetry/decay/grid determinism, directed graph edges, third-player routes, opportunity ordering, blocked-triangle penalties, immutable counterfactual comparisons, all interaction signs, fixture behavior, and all four API routes.

Run the performance harness separately:

```bash
python scripts/benchmark.py
```

Benchmark numbers are machine-specific and are not correctness thresholds. Full snapshot latency should remain comfortably interactive before any premature optimization.

The 2026-10-10 local reference run used Python 3.14.3 with 25 main iterations and 5 grid iterations: triangle detection `0.73 ms`, pressure grid `2.15 ms`, full snapshot analysis `32.21 ms`, and four-state interaction `86.39 ms` on the development machine.
