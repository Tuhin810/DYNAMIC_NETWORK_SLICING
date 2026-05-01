# Architecture Overview

## Purpose
This repository is a 5G network slicing simulation and research pipeline. It models mixed traffic from IoT, video, and emergency devices, assigns those devices to slices, simulates performance, and exports reproducible experiment artifacts for paper-style analysis.

## Main Flow
1. Generate virtual devices with deterministic seeds.
2. Choose a slicing policy: static, dynamic, or PSDAS.
3. Simulate latency, throughput, packet loss, SLA violations, fairness, and utility.
4. Run single experiments from the CLI or large scenario-by-seed experiment batches.
5. Aggregate results into tables, significance tests, figures, and manuscript text.

## Core Layers
- Device generation: `devices.py` and `scenarios.py` create repeatable device populations and fixed traffic presets.
- Allocation policies: `slicing.py` contains static, dynamic, and PSDAS assignment logic.
- Simulation: `simulation.py` turns assignments into per-device and per-slice metrics.
- Presentation: `visualization.py` and `plot_experiment_graphs.py` create comparison plots.
- Research pipeline: `run_experiments.py` and `day3_analyze_results.py` build the reproducible evaluation workflow.

## Key Idea
The project is not just a simulator. It is a full research artifact pipeline around one novel policy: PSDAS, which combines short-horizon prediction, SLA debt tracking, and adaptive objective weighting.

## Data Flow
The flow is:
`scenario -> device generation -> slicing policy -> simulation -> CSV/JSON outputs -> statistical analysis -> figures and paper draft`

## Outputs
The repository produces:
- Per-run device metrics CSV files
- Per-slice summary CSV files
- Run metadata JSON files
- Aggregated run summaries
- Markdown comparison tables
- Paper-ready figures
- A manuscript draft and reproduction guide
