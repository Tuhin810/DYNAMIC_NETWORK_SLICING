# File-by-File Walkthrough

## Top-Level Scripts

### `main.py`
Interactive and command-line entry point for one-off runs.
- Lets the user choose static, dynamic, PSDAS, or compare mode.
- Generates devices, runs the chosen slicing policy, and prints summary KPIs.
- In compare mode, it also creates latency and throughput plots.

### `run_experiments.py`
Batch experiment runner for reproducible research runs.
- Iterates over scenario, algorithm, and seed combinations.
- Supports `static`, `dynamic`, and `psdas`.
- Writes per-run artifacts plus aggregated `runs_summary.csv` and `baseline_comparison.md`.
- Records PSDAS parameters and ablation labels in metadata.

### `day3_analyze_results.py`
Analysis and figure-generation pipeline for the larger evaluation.
- Loads experiment summaries.
- Computes aggregate metrics and 95 percent confidence intervals.
- Runs paired PSDAS-vs-dynamic significance tests.
- Produces ablation-impact tables and paper-ready figures.

### `plot_experiment_graphs.py`
Generic plotting utility for experiment summaries.
- Builds comparison plots from a `runs_summary.csv` file.
- Can optionally compare a current run set to a previous one.
- Produces metric dashboards and delta plots.

## Simulation and Policy Modules

### `devices.py`
Defines the `Device` model and the baseline random device generator.
- Samples IoT, video, and emergency traffic.
- Assigns data rate and priority values.
- Enforces the minimum device-count constraint.

### `scenarios.py`
Defines fixed experiment scenarios and reproducible run configuration objects.
- Stores scenario presets such as `balanced`, `video_heavy`, `emergency_burst`, `high_congestion`, and `noisy_channel`.
- Generates scenario-specific device populations.
- Records the full run configuration for metadata export.

### `slicing.py`
Contains all slice allocation logic.
- Defines slice profiles for `mMTC`, `eMBB`, and `URLLC`.
- Implements static assignment by device type.
- Implements the dynamic heuristic using load and priority.
- Implements PSDAS, including prediction, SLA debt, overload guarding, and ablations.

### `simulation.py`
Computes performance outcomes for a given assignment.
- Produces per-device latency, throughput, and packet loss.
- Aggregates per-slice summaries with average, p95, and p99 latency.
- Counts SLA violations and computes fairness and utility scores.
- Applies slice-specific SLA thresholds for `mMTC`, `eMBB`, and `URLLC`.

### `visualization.py`
Creates simple comparison plots for the interactive compare mode.
- Generates grouped bar charts for latency and throughput.
- Currently compares static vs dynamic results.

## Documentation and Research Artifacts

### `README.md`
Primary project entry document.
- Explains the simulator and the research pipelines.
- Lists run commands for baseline, PSDAS, and Day 3 evaluation.
- Points to expected output files.

### `REPRODUCE.md`
Reproducibility guide for the paper-quality artifacts.
- Lists exact commands to regenerate the Day 3 and Day 4 outputs.
- Maps claims to generated files.
- Gives sanity checks for counts and output presence.

### `PAPER_DRAFT.md`
Draft manuscript skeleton populated with actual results.
- Includes abstract, method, experimental setup, results, ablation study, and limitations.
- Summarizes the main PSDAS claims.

### `DAY*_DELIVERABLES_DETAILED.md`
Progress reports for the 4-day sprint.
- Document what was built on each day.
- Explain the research reasoning behind each addition.
- Link implementation to evaluation output.

## Output Directories

### `outputs/`
Contains generated experiment and analysis artifacts.
- `experiments/` and later research variants store run outputs.
- `paper_figures/` stores publication-style figures.
- Subdirectories hold scenario, algorithm, seed, and report outputs.

## Overall Structure
The codebase is organized as a small simulator core plus a larger research wrapper around it. The simulator handles device generation, slicing, and metric computation. The research wrapper adds scenario control, repeated experiments, statistical analysis, plots, and paper-ready documentation.
