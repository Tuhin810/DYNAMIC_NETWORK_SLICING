# Day 3 Deliverables Report (Research Sprint)

## Day 3 Goal
Generate end-to-end evaluation evidence for PSDAS with:

1. Full experiment matrix at research scale.
2. Statistical significance and effect-size reporting.
3. Paper-ready figures and interpretation notes.

This day is complete.

---

## What Was Implemented

## 1) Production-Scale Experiment Runs

Executed full matrix with 30 seeds across all 5 scenarios for:

- `static`
- `dynamic`
- `psdas`

Total base runs:

- 5 scenarios x 3 algorithms x 30 seeds = 450 runs.

Executed ablation matrices with 30 seeds each:

- `psdas_no_prediction`
- `psdas_no_debt`
- `psdas_fixed_weights`

Total ablation runs:

- 5 scenarios x 1 algorithm x 30 seeds x 3 variants = 450 runs.

Grand total Day 3 runs:

- 900 runs.

---

## 2) Day 3 Analysis Pipeline Added

Implemented `day3_analyze_results.py` to produce:

1. Aggregate metric tables with mean and 95% CI.
2. PSDAS vs Dynamic paired statistical testing:
   - two-sided paired permutation p-value
   - paired effect size (Cohen dz)
3. Ablation impact tables against full PSDAS.
4. Paper-ready figure generation:
   - CI bar plots for key metrics
   - per-slice latency CDF
   - ablation comparison plots
5. One-page findings summary with interpretation notes and limits.

---

## 3) Novelty-Fidelity Fix Applied

Issue detected:

- `psdas_no_prediction` was initially near-identical to full PSDAS, indicating predictive signal under-use.

Fix implemented in `slicing.py`:

1. Added short-horizon trend-aware prediction update.
2. Updated projected predicted-load blending so prediction affects score computation.

Result:

- Prediction ablation is now behaviorally distinct and auditable.

---

## Key Statistical Outcomes (PSDAS vs Dynamic)

From `outputs/day3_research_v2/report/psdas_vs_dynamic_stats.md`:

1. `balanced`:
   - PSDAS wins significantly in 2/4 primary metrics.
2. `emergency_burst`:
   - PSDAS wins significantly in 2/4 primary metrics.
3. `high_congestion`:
   - PSDAS wins significantly in 2/4 primary metrics.
4. `noisy_channel`:
   - PSDAS wins significantly in 1/4 primary metrics.
5. `video_heavy`:
   - PSDAS wins significantly in 1/4 primary metrics.

Primary consistent strength:

- URLLC p95 latency reduction under stressed scenarios.

Primary limitation:

- Throughput-heavy objectives (especially eMBB throughput and utility in some regimes) still favor dynamic baseline.

---

## Generated Artifacts

Report artifacts:

- `outputs/day3_research_v2/report/aggregate_metrics.csv`
- `outputs/day3_research_v2/report/psdas_vs_dynamic_stats.csv`
- `outputs/day3_research_v2/report/psdas_vs_dynamic_stats.md`
- `outputs/day3_research_v2/report/ablation_impact.csv`
- `outputs/day3_research_v2/report/ablation_impact.md`
- `outputs/day3_research_v2/report/day3_findings_summary.md`

Paper figures:

- `outputs/paper_figures/day3_research_v2/fig1_sla_violation_ci.png`
- `outputs/paper_figures/day3_research_v2/fig2_utility_ci.png`
- `outputs/paper_figures/day3_research_v2/fig3_urllc_p95_ci.png`
- `outputs/paper_figures/day3_research_v2/fig4_latency_cdf_per_slice.png`
- `outputs/paper_figures/day3_research_v2/fig5_ablation_utility.png`
- `outputs/paper_figures/day3_research_v2/fig6_ablation_sla_violation.png`

---

## Commands Executed

Base matrix:

`/Users/tuhin/coding/project/.venv/bin/python run_experiments.py --scenarios all --algorithms static dynamic psdas --seed-count 30 --output-dir outputs/day3_research_v2/base`

Ablations:

1. `/Users/tuhin/coding/project/.venv/bin/python run_experiments.py --scenarios all --algorithms psdas --seed-count 30 --psdas-no-prediction --output-dir outputs/day3_research_v2/no_prediction`
2. `/Users/tuhin/coding/project/.venv/bin/python run_experiments.py --scenarios all --algorithms psdas --seed-count 30 --psdas-no-debt --output-dir outputs/day3_research_v2/no_debt`
3. `/Users/tuhin/coding/project/.venv/bin/python run_experiments.py --scenarios all --algorithms psdas --seed-count 30 --psdas-fixed-weights --output-dir outputs/day3_research_v2/fixed_weights`

Analysis and figure generation:

`/Users/tuhin/coding/project/.venv/bin/python day3_analyze_results.py --base-summary-csv outputs/day3_research_v2/base/runs_summary.csv --base-output-dir outputs/day3_research_v2/base --ablation-summary-csvs outputs/day3_research_v2/no_prediction/runs_summary.csv outputs/day3_research_v2/no_debt/runs_summary.csv outputs/day3_research_v2/fixed_weights/runs_summary.csv --paper-figures-dir outputs/paper_figures/day3_research_v2 --report-dir outputs/day3_research_v2/report`

---

## Day 3 Acceptance Checklist

1. Full experiment matrix (>=30 seeds) executed. Completed.
2. Aggregate stats and confidence intervals generated. Completed.
3. Publication-focused figures generated (6 total). Completed.
4. Figure interpretation notes and one-page findings summary generated. Completed.
5. Failure cases and limits identified. Completed.

Day 3 is complete and ready for Day 4 paper packaging.
