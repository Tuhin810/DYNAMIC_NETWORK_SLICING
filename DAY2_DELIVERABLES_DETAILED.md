# Day 2 Deliverables Report (Research Sprint)

## Day 2 Goal
Implement and integrate the novel slicing policy (PSDAS) with ablations and reproducible execution.

This day is complete.

---

## What Was Implemented

## 1) PSDAS Policy Implementation

Implemented in `slicing.py`:

- `assign_psdas_slices(...)` online allocator.
- `PsdasConfig` control dataclass.
- EWMA load prediction per slice.
- Class-slice SLA debt tracker (per traffic class x per slice).
- Adaptive multi-objective scoring (latency, throughput, packet loss).

Supporting helpers added:

- `_validate_psdas_config(...)`
- `_psdas_slice_score(...)`
- `_psdas_objective_weights(...)`
- `_estimate_projected_metrics(...)`
- `_estimate_sla_risk(...)`
- `_update_psdas_debt(...)`

Why it matters for paper:

- Introduces a clearly distinct policy beyond static and rule-based dynamic baselines.
- Encodes prediction, memory (debt), and adaptive objectives in a single online method.
- Provides direct knobs and ablations to support novelty claims.

---

## 2) Required Control Knobs and Ablations

Added PSDAS knobs:

1. `prediction_alpha`
2. `debt_gain`
3. `overload_guard`

Added ablation flags:

1. `--psdas-no-prediction`
2. `--psdas-no-debt`
3. `--psdas-fixed-weights`

Ablation labels are deterministic in outputs:

- `psdas_no_prediction`
- `psdas_no_debt`
- `psdas_fixed_weights`

Why it matters for paper:

- Enables component-level contribution analysis.
- Keeps comparisons auditable and machine-readable.

---

## 3) CLI Integration in main.py

Integrated PSDAS into single-run CLI:

- New mode: `--mode psdas`
- Menu now includes PSDAS option.
- PSDAS run path supports all knobs and ablation flags.

Why it matters for paper:

- Fast local validation of policy behavior before large experiment batches.

---

## 4) Batch Experiment Integration in run_experiments.py

Integrated PSDAS into reproducible matrix runner:

- `--algorithms` now supports `psdas`.
- PSDAS knobs and ablation flags available in batch CLI.
- Per-run metadata now includes `psdas_params` for PSDAS runs.
- Output directories and summary rows include specific PSDAS variant labels.

Why it matters for paper:

- Allows direct, reproducible scenario x algorithm x seed comparisons.
- Preserves traceability from method settings to run outputs.

---

## 5) Simulation Compatibility Update

Updated `simulation.py` so dynamic-style adjustments apply to:

- `dynamic`
- `psdas`
- any `psdas_*` ablation variant

via `_is_dynamic_mode(mode)`.

Why it matters for paper:

- Prevents unfair treatment of PSDAS as a static strategy during simulation.

---

## 6) Documentation Update

Updated `README.md`:

- Added PSDAS feature description.
- Added `psdas` mode and knob/ablation flags.
- Added Day 2 runner commands for full PSDAS and ablations.

---

## Executed Day 2 Smoke Runs

Single-run CLI smoke test:

`/Users/tuhin/coding/project/.venv/bin/python main.py --mode psdas --devices 120 --seed 7`

Batch smoke tests across all 5 scenarios with 1 seed each:

1. `/Users/tuhin/coding/project/.venv/bin/python run_experiments.py --scenarios all --algorithms static dynamic psdas --seed-count 1 --output-dir outputs/day2_smoke/base`
2. `/Users/tuhin/coding/project/.venv/bin/python run_experiments.py --scenarios all --algorithms psdas --seed-count 1 --psdas-no-prediction --output-dir outputs/day2_smoke/no_prediction`
3. `/Users/tuhin/coding/project/.venv/bin/python run_experiments.py --scenarios all --algorithms psdas --seed-count 1 --psdas-no-debt --output-dir outputs/day2_smoke/no_debt`
4. `/Users/tuhin/coding/project/.venv/bin/python run_experiments.py --scenarios all --algorithms psdas --seed-count 1 --psdas-fixed-weights --output-dir outputs/day2_smoke/fixed_weights`

Smoke outcome:

- All commands completed without crashes.
- Artifacts generated for all scenarios and requested algorithms/ablations.

---

## Day 2 Acceptance Checklist

1. Working PSDAS policy selectable from CLI. Completed.
2. Ablation-ready PSDAS implementation. Completed.
3. PSDAS integrated into batch runner. Completed.
4. Smoke tests executed across all scenario presets. Completed.
5. Outputs include comparable full metrics and metadata. Completed.

Day 2 is complete and experiment-ready for Day 3 evaluation.
