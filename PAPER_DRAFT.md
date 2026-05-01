# Predictive SLA-Debt Aware Slicing (PSDAS) for 5G Network Slicing

## Abstract
We present Predictive SLA-Debt Aware Slicing (PSDAS), an online policy for 5G network slicing that combines short-horizon load prediction, SLA-debt feedback, and adaptive objective weighting. Unlike static assignment and rule-based dynamic heuristics, PSDAS explicitly tracks recent service deficits and adapts allocation pressure accordingly. We evaluate PSDAS on five stress-tested traffic scenarios with 30 seeds each and compare against static and dynamic baselines. Results show statistically significant tail-latency and SLA-compliance gains in multiple regimes, with strongest benefits in URLLC p95 latency under congestion and bursty emergency load. We also provide ablation evidence showing the debt component contributes materially to utility improvements. The complete artifact package includes reproducible run scripts, per-run CSV/JSON outputs, and paper-ready figures.

## 1. Introduction
Network slicing in mixed 5G traffic must balance conflicting objectives across latency-critical, throughput-heavy, and reliability-sensitive services. Existing heuristic allocators are typically reactive and myopic, relying on current load or static priorities without explicit memory of unmet SLAs.

This work proposes PSDAS, a lightweight online allocator that introduces three mechanisms jointly:

1. Predictive load estimation for near-term congestion anticipation.
2. SLA debt tracking per class-slice pair to encode historical under-service.
3. Adaptive multi-objective weighting (latency, throughput, loss) conditioned on debt and traffic priority.

## 2. Related Work (Draft Positioning)
Prior heuristic approaches usually emphasize one dimension: fixed priority routing, load balancing, or static QoS thresholds. PSDAS differs by integrating predictive and history-aware control into a single online score with explicit ablations.

## 3. Method: PSDAS
### 3.1 Policy Components
1. Predictor: short-horizon trend-aware load estimate.
2. Debt: per class-slice SLA debt updated each allocation step.
3. Adaptive weighting: priority- and debt-conditioned objective mixing.

### 3.2 Allocation Objective
For each device and candidate slice, PSDAS minimizes a composite score combining:

1. Estimated latency penalty.
2. Estimated throughput penalty.
3. Estimated packet-loss penalty.
4. Mismatch, overload-guard, and debt penalties.
5. Policy preference bonuses.

### 3.3 Ablations
1. No prediction: `psdas_no_prediction`
2. No debt: `psdas_no_debt`
3. Fixed weights: `psdas_fixed_weights`

## 4. Experimental Setup
### 4.1 Scenarios
1. `balanced`
2. `video_heavy`
3. `emergency_burst`
4. `high_congestion`
5. `noisy_channel`

### 4.2 Baselines
1. `static`
2. `dynamic`
3. `psdas`

### 4.3 Protocol
1. 30 seeds per scenario-algorithm configuration.
2. Paired PSDAS-vs-dynamic statistical comparison by common seed.
3. Two-sided paired permutation p-value and Cohen dz effect size.

## 5. Results
### 5.1 PSDAS vs Dynamic (Primary Metrics)
From `outputs/day3_research_v2/report/psdas_vs_dynamic_stats.md`:

1. `balanced`
- SLA violation: 99.2962 -> 97.6111 (PSDAS, p=0.0001).
- URLLC p95 latency: 19.7078 -> 18.6864 ms (PSDAS, p=0.0006).
- Utility and eMBB throughput favored dynamic.

2. `emergency_burst`
- SLA violation: 99.7593 -> 97.5926 (PSDAS, p=0.0001).
- URLLC p95 latency: 20.7646 -> 19.0748 ms (PSDAS, p=0.0001).
- Utility and eMBB throughput favored dynamic.

3. `high_congestion`
- Utility: 0.1717 -> 0.1747 (PSDAS, p=0.0001).
- URLLC p95 latency: 31.9053 -> 24.6729 ms (PSDAS, p=0.0001).
- eMBB throughput favored dynamic.

4. `noisy_channel`
- URLLC p95 latency: 24.2596 -> 20.9542 ms (PSDAS, p=0.0001).
- SLA and utility differences vs dynamic were not significant.

5. `video_heavy`
- URLLC p95 latency: 37.1854 -> 26.6285 ms (PSDAS, p=0.0001).
- Utility and eMBB throughput favored dynamic.

### 5.2 Interpretation
PSDAS provides robust gains for latency-critical behavior (especially URLLC tails) and selective SLA-rate improvements, but the current weighting regime sacrifices eMBB throughput in several scenarios.

### 5.3 Figure Set
1. `outputs/paper_figures/day3_research_v2/fig1_sla_violation_ci.png`
2. `outputs/paper_figures/day3_research_v2/fig2_utility_ci.png`
3. `outputs/paper_figures/day3_research_v2/fig3_urllc_p95_ci.png`
4. `outputs/paper_figures/day3_research_v2/fig4_latency_cdf_per_slice.png`
5. `outputs/paper_figures/day3_research_v2/fig5_ablation_utility.png`
6. `outputs/paper_figures/day3_research_v2/fig6_ablation_sla_violation.png`

## 6. Ablation Study
From `outputs/day3_research_v2/report/ablation_impact.md`:

1. Removing debt (`psdas_no_debt`) causes the largest utility degradation:
- emergency_burst: +11.62%
- high_congestion: +11.42%
- noisy_channel: +11.17%
- balanced: +9.94%
- video_heavy: +7.90%

2. Removing prediction (`psdas_no_prediction`) has small but measurable effects in multiple scenarios.
3. Fixed weights are close to full PSDAS in most scenarios, suggesting debt dominates current gains.

## 7. Limitations and Failure Cases
1. Throughput-heavy metrics remain a weakness versus dynamic heuristics.
2. Several metrics saturate near 100% SLA violation in severe load regimes, reducing discriminative power.
3. Predictor contribution is currently smaller than debt contribution, suggesting room for stronger forecast integration.

## 8. Novelty Defense (for Submission)
1. PSDAS is not only priority assignment: it introduces historical SLA debt as explicit feedback control.
2. PSDAS is not only load balancing: it includes short-horizon prediction and adaptive objective reweighting.
3. Ablation evidence isolates component contributions, especially debt impact on utility.
4. Stress-scenario matrix and statistical protocol provide auditable evidence, not anecdotal wins.

## 9. Reproducibility Statement
All commands, environment setup, and artifact map are provided in `REPRODUCE.md`. Each claim in Section 5 maps to generated CSV/markdown tables and figure files.

## 10. Future Work
1. Pareto-aware dynamic weighting to recover eMBB throughput without losing URLLC gains.
2. Multi-step forecasting beyond one-step trend estimation.
3. Scenario-adaptive debt gains and guard thresholds.
4. Additional robustness metrics under channel perturbation and mobility.
