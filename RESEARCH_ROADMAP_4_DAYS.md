# 4-Day Research Sprint Roadmap

## Objective
In 4 days, convert this simulator into a research-grade artifact with:

1. A clearly novel dynamic slicing method.
2. Reproducible experiments and statistical evidence.
3. Paper-ready figures, tables, and writing structure.

Primary codebase anchors:
- `devices.py` for workload generation.
- `slicing.py` for baseline and new policy logic.
- `simulation.py` for metric generation.
- `visualization.py` for publication plots.
- `main.py` for experiment entry points.

---

## Proposed Novelty (Unique Angle)

### Method Name
Predictive SLA-Debt Aware Slicing (PSDAS)

### Core Idea
Most heuristic slicing methods react to current load only. PSDAS combines 3 elements in one online policy:

1. Short-horizon load prediction (EWMA) to anticipate congestion.
2. SLA debt tracking per slice/class (how far recent performance is from SLA target).
3. Adaptive multi-objective weighting (latency vs throughput vs loss) driven by debt and traffic priority.

### Why This Is Novel Enough
- It is not only priority-aware assignment.
- It is not only load balancing.
- It introduces memory of unmet SLA (debt), predictive control, and adaptive objective weights in a single policy.
- It is easy to ablate, so novelty can be proven experimentally.

### Minimal Contribution Claims for Paper
1. A new online slicing policy using predictive SLA-debt feedback.
2. A stress-test framework with bursty emergency and mixed traffic regimes.
3. Quantified gains over static and rule-based dynamic baselines with confidence intervals.

---

## Target Metrics (Research-Level)
Keep existing metrics and add:

1. p95 and p99 latency per slice.
2. SLA violation rate per slice and overall.
3. Jain fairness index on achieved throughput across slices.
4. Utility score (weighted sum of normalized latency, throughput, packet loss).
5. Robustness score under burst scenarios.

SLA template (can be tuned):
- URLLC: latency p95 <= 10 ms, packet loss <= 1%
- eMBB: throughput >= 25 Mbps average
- mMTC: packet loss <= 3%, latency p95 <= 80 ms

---

## Experiment Matrix (Must Run)

Scenarios:
1. Normal balanced traffic.
2. Video-heavy load.
3. Emergency burst every N steps.
4. High background congestion.
5. Noisy channel stress (stochastic degradation).

Baselines:
1. Static assignment (existing).
2. Current dynamic heuristic (existing).
3. PSDAS (new).

Repetitions:
- At least 30 seeds per scenario.

Statistical reporting:
- Mean and 95% confidence interval.
- Effect size and p-value for PSDAS vs current dynamic.

---

## 4-Day Execution Plan

## Day 1 - Research Foundation + Instrumentation

### Goal
Make experiments reproducible and paper-auditable.

### Tasks
1. Add a run config object (scenario, devices, seed, load profile, algorithm).
2. Add structured output export:
   - per-device metrics CSV
   - per-slice summary CSV
   - run metadata JSON
3. Extend metrics in `simulation.py`:
   - p95/p99 latency
   - SLA violation counters
   - fairness index
4. Add scenario generator module for fixed scenario presets.
5. Add `run_experiments.py` to execute batches by scenario and seed.

### Deliverables (End of Day)
1. Repeatable command that runs all baseline experiments.
2. `outputs/experiments/` with machine-readable artifacts.
3. Initial table comparing static vs current dynamic across at least 3 scenarios.

### Definition of Done
- Same seed gives same outputs.
- One command runs all baseline experiments without manual edits.

---

## Day 2 - Implement the Novel Algorithm (PSDAS)

### Goal
Implement and integrate a clearly new slicing policy.

### Tasks
1. Add `psdas_allocate(...)` policy in `slicing.py` or a new `novel_slicing.py`.
2. Implement components:
   - EWMA load predictor per slice.
   - SLA debt tracker updated each interval.
   - Adaptive objective weights from debt and priority.
3. Add control knobs:
   - prediction_alpha
   - debt_gain
   - overload_guard
4. Integrate policy option into `main.py` and experiment runner.
5. Add ablation flags:
   - no prediction
   - no debt
   - fixed weights

### Deliverables (End of Day)
1. Working PSDAS policy selectable from CLI.
2. Ablation-ready version for contribution proof.
3. Smoke test results showing policy executes across all scenarios.

### Definition of Done
- PSDAS runs without crashes on all scenario presets.
- Outputs include full metrics comparable against baselines.

---

## Day 3 - Evaluation, Statistics, and Figures

### Goal
Generate evidence that novelty improves key outcomes.

### Tasks
1. Run full experiment matrix (>=30 seeds each scenario).
2. Compute aggregate stats and confidence intervals.
3. Create publication-focused plots:
   - CDF of latency per slice
   - bar plots with CI
   - SLA violation comparison
   - ablation study chart
4. Write short interpretation notes for each figure.
5. Identify failure cases and limits of PSDAS.

### Deliverables (End of Day)
1. Final result tables (CSV + markdown).
2. 4-6 paper-quality figures in `outputs/paper_figures/`.
3. A one-page findings summary with key numbers.

### Definition of Done
- Every claim has a matching figure/table.
- Novel method beats dynamic baseline in at least 2 primary metrics with significance.

---

## Day 4 - Paper Packaging + Reproducibility

### Goal
Finish research-level package ready for drafting/submission.

### Tasks
1. Create `PAPER_DRAFT.md` skeleton:
   - Abstract
   - Introduction
   - Related Work
   - Method (PSDAS)
   - Experimental Setup
   - Results
   - Ablation
   - Limitations and Future Work
2. Fill results section using Day 3 artifacts.
3. Add reproducibility section:
   - environment
   - commands
   - data/artifact map
4. Add `REPRODUCE.md` with exact commands.
5. Prepare novelty defense bullets (what is new vs prior heuristic methods).

### Deliverables (End of Day)
1. Complete draft manuscript structure with populated results.
2. Reproducibility checklist and scripts.
3. Submission-ready artifact package (code + figures + tables + commands).

### Definition of Done
- Another person can reproduce main figures using documented commands.
- Paper draft has no missing technical sections.

---

## Daily Work Cadence (Recommended)
For each day, use fixed blocks:

1. 2 hours implementation.
2. 1 hour validation and debugging.
3. 1 hour experiment runs.
4. 1 hour analysis and writing notes.

Keep a running log file:
- `DAILY_LOG_DAY1.md`
- `DAILY_LOG_DAY2.md`
- `DAILY_LOG_DAY3.md`
- `DAILY_LOG_DAY4.md`

Each log should include:
1. What changed.
2. What worked.
3. What failed.
4. Exact next action.

---

## Risk Register and Mitigation

1. Risk: Novel method does not beat baseline consistently.
Mitigation: tune debt gain and overload guard; focus claim on robustness and SLA compliance, not all metrics.

2. Risk: Runtime too slow for full matrix.
Mitigation: parallel seed runs and cache intermediate outputs.

3. Risk: Claims look incremental.
Mitigation: include ablation and stress tests proving each PSDAS component matters.

4. Risk: Reproducibility gaps.
Mitigation: freeze dependencies and keep single-command scripts.

---

## Acceptance Checklist for Research-Level Completion

1. Novel method fully implemented and documented.
2. Baseline comparison across all scenarios complete.
3. Statistical significance reported.
4. Ablation study complete.
5. Paper draft sections complete with figures and tables.
6. Reproduction instructions verified end to end.

If all six are checked by Day 4, the project is at research-paper level.