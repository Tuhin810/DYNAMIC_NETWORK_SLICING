# Reproduce Day 3 and Day 4 Artifacts

## 1) Environment
Tested on macOS with Python virtual environment in this repository.

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

If using the project venv directly:

```bash
/Users/tuhin/coding/project/.venv/bin/python -m pip install -r requirements.txt
```

## 2) Run Full Day 3 Matrix (Base)

```bash
/Users/tuhin/coding/project/.venv/bin/python run_experiments.py \
  --scenarios all \
  --algorithms static dynamic psdas \
  --seed-count 30 \
  --output-dir outputs/day3_research_v2/base
```

Expected size:

1. 450 runs total.
2. `outputs/day3_research_v2/base/runs_summary.csv` exists.

## 3) Run PSDAS Ablations

```bash
/Users/tuhin/coding/project/.venv/bin/python run_experiments.py --scenarios all --algorithms psdas --seed-count 30 --psdas-no-prediction --output-dir outputs/day3_research_v2/no_prediction
/Users/tuhin/coding/project/.venv/bin/python run_experiments.py --scenarios all --algorithms psdas --seed-count 30 --psdas-no-debt --output-dir outputs/day3_research_v2/no_debt
/Users/tuhin/coding/project/.venv/bin/python run_experiments.py --scenarios all --algorithms psdas --seed-count 30 --psdas-fixed-weights --output-dir outputs/day3_research_v2/fixed_weights
```

Expected size:

1. 150 runs per ablation directory.
2. Each directory contains `runs_summary.csv`.

## 4) Generate Statistics and Figures

```bash
/Users/tuhin/coding/project/.venv/bin/python day3_analyze_results.py \
  --base-summary-csv outputs/day3_research_v2/base/runs_summary.csv \
  --base-output-dir outputs/day3_research_v2/base \
  --ablation-summary-csvs \
    outputs/day3_research_v2/no_prediction/runs_summary.csv \
    outputs/day3_research_v2/no_debt/runs_summary.csv \
    outputs/day3_research_v2/fixed_weights/runs_summary.csv \
  --paper-figures-dir outputs/paper_figures/day3_research_v2 \
  --report-dir outputs/day3_research_v2/report
```

## 5) Artifact Map

### Statistical tables
1. `outputs/day3_research_v2/report/aggregate_metrics.csv`
2. `outputs/day3_research_v2/report/psdas_vs_dynamic_stats.csv`
3. `outputs/day3_research_v2/report/psdas_vs_dynamic_stats.md`
4. `outputs/day3_research_v2/report/ablation_impact.csv`
5. `outputs/day3_research_v2/report/ablation_impact.md`
6. `outputs/day3_research_v2/report/day3_findings_summary.md`

### Figures
1. `outputs/paper_figures/day3_research_v2/fig1_sla_violation_ci.png`
2. `outputs/paper_figures/day3_research_v2/fig2_utility_ci.png`
3. `outputs/paper_figures/day3_research_v2/fig3_urllc_p95_ci.png`
4. `outputs/paper_figures/day3_research_v2/fig4_latency_cdf_per_slice.png`
5. `outputs/paper_figures/day3_research_v2/fig5_ablation_utility.png`
6. `outputs/paper_figures/day3_research_v2/fig6_ablation_sla_violation.png`

## 6) Claim-to-Artifact Traceability

1. PSDAS vs dynamic significance claims:
- `outputs/day3_research_v2/report/psdas_vs_dynamic_stats.md`

2. Component contribution claims (ablations):
- `outputs/day3_research_v2/report/ablation_impact.md`

3. Scenario-level summary claims:
- `outputs/day3_research_v2/report/day3_findings_summary.md`

4. Plot-level visual evidence:
- `outputs/paper_figures/day3_research_v2/*.png`

## 7) Optional Sanity Checks

Check key outputs exist:

```bash
ls outputs/day3_research_v2/report
ls outputs/paper_figures/day3_research_v2
```

Check row counts quickly (example):

```bash
wc -l outputs/day3_research_v2/base/runs_summary.csv
wc -l outputs/day3_research_v2/no_prediction/runs_summary.csv
```

Expected approximate lines including header:

1. Base summary: 451 lines.
2. Each ablation summary: 151 lines.
