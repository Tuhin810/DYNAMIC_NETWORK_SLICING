# Research-Level Upgrade Plan for PSDAS

## 1. Purpose
This document defines what it takes to move the current PSDAS project from strong simulation evidence to journal-grade research quality.

Target profile:
1. Venue level: Journal paper.
2. Scope: Full major upgrade (method, baselines, statistics, writing).
3. Default claim: Balanced trade-off (retain URLLC gains while reducing eMBB loss).

## 2. Research-Level Checklist
A practical paper-level bar is met only when all items below are green.

| Criterion | Current Status | Required for Journal-Grade |
|---|---|---|
| Reproducible pipeline | Good | Keep exact commands and deterministic seed pairing |
| Statistical rigor | Partial | Add multiple-testing correction and adjusted significance reporting |
| Baseline strength | Weak | Add optimization and learning-based baselines beyond rule heuristics |
| Method clarity | Partial | Add equations/pseudocode and tighter mechanism definitions |
| External validity | Weak | Add realism calibration or real trace validation path |
| Trade-off handling | Weak | Show clear latency-throughput frontier and balanced operating point |
| Related work depth | Partial | Expand with direct method-to-method positioning |
| Claims traceability | Good | Keep claim-to-artifact mapping for every reported number |

## 3. Current Gap Matrix

| Gap | Why Reviewers Will Flag It | File-Level Upgrade Path |
|---|---|---|
| eMBB throughput loss vs dynamic | Strong URLLC gains alone may be seen as one-sided | Update scoring/weights in slicing.py and add Pareto analysis in day3_analyze_results.py |
| Prediction contribution is small in ablation | "Predictive" claim can appear overstated | Strengthen prediction module in slicing.py and rerun ablation evidence |
| Baselines are too limited | Static + one heuristic is not enough for journal bar | Add optimization baseline and DRL baseline, wire in run_experiments.py |
| No correction for multiple comparisons | 20+ tests without correction risks false positives | Add Holm-Bonferroni in day3_analyze_results.py |
| Related work section is shallow | Novelty can be judged unclear | Expand PAPER_DRAFT.md with method-level comparisons |
| External validity not established | Simulation-only evidence is a common rejection point | Add calibration/trace validation notes in PAPER_DRAFT.md and REPRODUCE.md |

## 4. Published-Paper Backing and Repo Adoption Map
The papers below are selected because they are highly relevant to slicing, resource allocation, and URLLC/eMBB trade-offs.

| Paper | Venue/Year | DOI | Why It Matters | How to Adopt Here |
|---|---|---|---|---|
| Network Slicing in 5G: Survey and Challenges | IEEE Communications Magazine, 2017 | https://doi.org/10.1109/MCOM.2017.1600951 | Canonical slicing problem framing and challenge taxonomy | Use in PAPER_DRAFT.md Section 2 to formalize problem positioning |
| Network Slicing and Softwarization: A Survey on Principles, Enabling Technologies, and Solutions | IEEE Communications Surveys and Tutorials, 2018 | https://doi.org/10.1109/COMST.2018.2815638 | Strong architecture and orchestration background | Use as reference backbone for system assumptions and orchestration language |
| Network Slicing for Guaranteed Rate Services: Admission Control and Resource Allocation Games | IEEE Transactions on Wireless Communications, 2018 | https://doi.org/10.1109/TWC.2018.2859918 | Optimization/game-theoretic baseline direction | Add an optimization-style baseline to run_experiments.py |
| Multi-Tenant Cross-Slice Resource Orchestration: A Deep Reinforcement Learning Approach | IEEE Journal on Selected Areas in Communications, 2019 | https://doi.org/10.1109/JSAC.2019.2933893 | High-impact DRL orchestration reference | Add one DRL baseline and compare against PSDAS across all scenarios |
| eMBB-URLLC Resource Slicing: A Risk-Sensitive Approach | IEEE Communications Letters, 2019 | https://doi.org/10.1109/LCOMM.2019.2900044 | Directly addresses tail risk in mixed traffic coexistence | Add risk-sensitive metric and policy penalty in simulation.py and slicing.py |
| Intelligent Resource Slicing for eMBB and URLLC Coexistence in 5G and Beyond: A Deep Reinforcement Learning Based Approach | IEEE Transactions on Wireless Communications, 2021 | https://doi.org/10.1109/TWC.2021.3060514 | Strong coexistence-focused DRL reference | Use as target baseline for balanced trade-off analysis |
| Deep Reinforcement Learning-Based Network Slicing for Beyond 5G | IEEE Access, 2022 | https://doi.org/10.1109/ACCESS.2022.3141789 | Practical DRL implementation style for slicing | Use for lightweight DRL baseline implementation choices |
| Deep Reinforcement Learning for Online Resource Allocation in Network Slicing | IEEE Transactions on Mobile Computing, 2024 | https://doi.org/10.1109/TMC.2023.3328950 | Modern online RL allocation benchmark direction | Use to justify online policy comparison design and analysis style |

## 5. Implementation Roadmap (Priority Order)

### Phase A: Statistical and Reporting Hardening (immediate)
1. Add Holm-Bonferroni adjusted p-values to PSDAS vs dynamic significance outputs.
2. Update markdown reports to show both raw and adjusted significance.
3. Update findings summary logic to prioritize adjusted significance.

Primary files:
1. day3_analyze_results.py

Acceptance criteria:
1. psdas_vs_dynamic_stats.csv contains adjusted p-values.
2. psdas_vs_dynamic_stats.md shows raw and adjusted significance columns.
3. day3_findings_summary.md reports adjusted-significance outcomes by scenario.

### Phase B: Balanced Trade-Off Mechanism Upgrade
1. Add explicit throughput-protection and Pareto-style weight adaptation in PSDAS scoring.
2. Keep debt mechanism interpretable and auditable.
3. Add parameter sweep options for trade-off coefficients.

Primary files:
1. slicing.py
2. run_experiments.py

Acceptance criteria:
1. URLLC p95 gains remain positive in high_congestion and emergency_burst.
2. eMBB throughput gap vs dynamic is reduced versus current PSDAS.
3. Ablation still shows meaningful separation of components.

### Phase C: Stronger Baselines
1. Add one optimization baseline.
2. Add one learning-based baseline (lightweight DRL).
3. Integrate new baselines into full matrix execution and reporting.

Primary files:
1. run_experiments.py
2. slicing.py or new baseline modules
3. day3_analyze_results.py

Acceptance criteria:
1. New baselines are first-class algorithms in experiment runs.
2. Output reports include PSDAS vs all strong baselines.
3. Claim section in PAPER_DRAFT.md is updated to include stronger comparisons.

### Phase D: Manuscript and Validity Upgrade
1. Expand related work with method-level contrasts, not only generic narrative.
2. Add clear threats-to-validity subsection.
3. Maintain strict claim-to-artifact mapping.

Primary files:
1. PAPER_DRAFT.md
2. REPRODUCE.md

Acceptance criteria:
1. Each major claim cites a concrete generated artifact path.
2. Related-work section explains exactly what PSDAS adds relative to each class of methods.

## 6. Immediate Execution Commands
After Phase A code changes, rerun analysis with the existing outputs:

```bash
python3 day3_analyze_results.py \
  --base-summary-csv outputs/day3_research_v2/base/runs_summary.csv \
  --base-output-dir outputs/day3_research_v2/base \
  --ablation-summary-csvs \
    outputs/day3_research_v2/no_prediction/runs_summary.csv \
    outputs/day3_research_v2/no_debt/runs_summary.csv \
    outputs/day3_research_v2/fixed_weights/runs_summary.csv \
  --paper-figures-dir outputs/paper_figures/day3_research_v2 \
  --report-dir outputs/day3_research_v2/report
```

Then verify:
1. outputs/day3_research_v2/report/psdas_vs_dynamic_stats.csv
2. outputs/day3_research_v2/report/psdas_vs_dynamic_stats.md
3. outputs/day3_research_v2/report/day3_findings_summary.md

## 7. Definition of Done (Journal-Ready Revision)
The revision is considered submission-ready when:
1. Balanced trade-off claim is supported by statistically robust evidence.
2. At least two strong baselines are included and discussed.
3. Multiple-testing correction is applied and reported.
4. Related work clearly positions PSDAS against optimization and DRL methods.
5. Reproducibility and claim traceability remain complete and executable.
