# Day 1 Deliverables Report (Research Sprint)

## Day 1 Goal
Build a reproducible, paper-auditable baseline experiment pipeline.

This day is complete.

---

## What Was Implemented

## 1) Reproducible Run Configuration

Implemented in `scenarios.py`:

- `ScenarioPreset` dataclass for fixed scenario definitions.
- `ExperimentRunConfig` dataclass for recording run-level parameters.
- Deterministic scenario list and lookup.
- Deterministic scenario-specific device generation tied to seed.

Why it matters for paper:
- Reviewers can see exact setup and replicate runs.
- Results are traceable to explicit scenario and seed.

---

## 2) Fixed Scenario Presets

Added fixed presets:

1. `balanced`
2. `video_heavy`
3. `emergency_burst`
4. `high_congestion`
5. `noisy_channel`

Why it matters for paper:
- You can claim evaluation across diverse operating regimes.
- This enables robustness analysis, not just one favorable case.

---

## 3) Research-Grade Metrics in Simulation

Extended `simulation.py` with:

1. p95 latency per slice.
2. p99 latency per slice.
3. SLA violation count per slice.
4. SLA violation rate per slice.
5. Overall SLA violation count and rate.
6. Jain fairness index (across slice throughput totals).
7. Utility score (bounded composite metric).

SLA threshold model added:

- mMTC: max latency, max packet loss.
- eMBB: min throughput, max packet loss.
- URLLC: max latency, max packet loss.

Why it matters for paper:
- Average-only metrics are weak for publication.
- Tail latency and SLA violation are publication-standard evidence for QoS systems.

---

## 4) Batch Experiment Runner

Implemented `run_experiments.py`:

- Runs scenario x algorithm x seed matrix.
- Supports static and dynamic baselines.
- Produces per-run machine-readable artifacts.
- Produces aggregated summary and markdown comparison table.

Why it matters for paper:
- Enables large-scale repeated experiments quickly.
- Creates a clean evidence pipeline for tables and plots.

---

## 5) Structured Experiment Outputs

For every run, exported:

1. `device_metrics.csv`
2. `slice_summary.csv`
3. `run_metadata.json`

Global outputs:

1. `outputs/experiments/runs_summary.csv`
2. `outputs/experiments/baseline_comparison.md`

Why it matters for paper:
- Full traceability from raw per-device data to final claims.
- Easy to re-aggregate, re-plot, and run significance tests.

---

## Executed Day 1 Run

Command executed:

`python run_experiments.py --seed-count 10`

Completed:

- 60 runs total.
- 3 scenarios (`balanced`, `video_heavy`, `emergency_burst`).
- 2 algorithms (`static`, `dynamic`).
- 10 seeds each combination.

This satisfies Day 1 baseline requirement of at least 3 scenarios with repeatable outputs.

---

## Baseline Snapshot (From Day 1 Artifacts)

From `outputs/experiments/baseline_comparison.md`:

- Balanced:
  - Dynamic utility: 0.2808
  - Static utility: 0.2465
- Emergency burst:
  - Dynamic utility: 0.2766
  - Static utility: 0.2674
- Video heavy:
  - Dynamic utility: 0.1831
  - Static utility: 0.1759

Interpretation:
- Current dynamic baseline shows utility gains but also high SLA violation rates under current strict thresholds.
- This is a useful paper setup: it exposes a real baseline weakness that your novel method can target directly.

---

## How to Explain Day 1 in Your Paper

Use this structure in Method/Experimental Setup sections:

1. Reproducibility protocol.
2. Scenario definitions and rationale.
3. Metrics (tail latency, SLA, fairness, utility).
4. Baseline execution matrix (seeds and algorithms).
5. Artifact generation pipeline.

Suggested writing text (adapt as needed):

"We established a reproducible baseline framework with deterministic scenario presets and seed-controlled traffic generation. For each run, we exported per-device and per-slice artifacts, including p95/p99 latency and SLA violation rates, enabling complete traceability from raw simulation outputs to aggregate claims. Baseline evaluation was conducted over three representative scenarios and multiple seeds to characterize variance before introducing the proposed method."

---

## Day 1 Acceptance Checklist

1. Fixed scenario presets implemented. Completed.
2. Run config object implemented. Completed.
3. Structured CSV/JSON exports implemented. Completed.
4. New research metrics implemented. Completed.
5. Batch baseline runner implemented. Completed.
6. Initial multi-scenario baseline results generated. Completed.

Day 1 is complete and research-ready.

---

## What Day 2 Can Start Immediately

1. Implement PSDAS allocator.
2. Plug PSDAS into `run_experiments.py` as third algorithm.
3. Add ablations: no prediction, no debt, fixed weights.
4. Reuse Day 1 pipeline for fair comparison.