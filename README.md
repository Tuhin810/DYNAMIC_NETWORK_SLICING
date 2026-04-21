# 5G Network Slicing Simulation Project

This project simulates **5G network slicing** for mixed traffic from:

- IoT devices
- Video devices
- Emergency devices

It is designed as a modular base for final year engineering projects and early-stage research.

## Project Structure

- `main.py` - Entry point and CLI menu
- `devices.py` - Virtual device generation
- `slicing.py` - Static and dynamic slice allocation logic
- `simulation.py` - Latency, throughput, and packet-loss simulation
- `visualization.py` - Matplotlib comparison graphs
- `scenarios.py` - Fixed scenario presets and experiment run config objects
- `run_experiments.py` - Reproducible batch experiment runner with CSV/JSON exports

## Slice Profiles

- **mMTC**: low bandwidth, high device capacity (IoT-oriented)
- **eMBB**: high bandwidth (video-oriented)
- **URLLC**: ultra-low latency (emergency-oriented)

## Features

- Generates at least 100 virtual devices with:
  - id
  - type (`iot`, `video`, `emergency`)
  - data rate
  - priority (1 high -> 3 low)
- Static assignment by device type
- Dynamic assignment using:
  - background network load
  - priority-aware scoring
- PSDAS assignment using:
  - EWMA load prediction
  - SLA debt tracking per class/slice
  - adaptive objective weighting
- Simulates:
  - latency
  - throughput
  - packet loss
- Prints slice summaries and strategy differences
- Creates graphs:
  - latency comparison
  - throughput comparison

## Setup

```bash
python3 -m pip install -r requirements.txt
```

## Run

Interactive menu:

```bash
python3 main.py
```

Direct mode:

```bash
python3 main.py --mode compare --devices 150 --seed 7
```

Mode options:

- `static`
- `dynamic`
- `psdas`
- `compare`
- `menu` (default)

PSDAS tuning/ablation flags (with `--mode psdas`):

- `--prediction-alpha`
- `--debt-gain`
- `--overload-guard`
- `--psdas-no-prediction`
- `--psdas-no-debt`
- `--psdas-fixed-weights`

## Output

When running in `compare` mode, plots are saved in `outputs/`:

- `latency_comparison.png`
- `throughput_comparison.png`

## Day 1 Research Pipeline

Run reproducible baseline experiments (static + dynamic) with structured artifacts:

```bash
python3 run_experiments.py --seed-count 10
```

This generates:

- `outputs/experiments/runs_summary.csv` (all runs)
- `outputs/experiments/baseline_comparison.md` (quick paper table)
- `outputs/experiments/<scenario>/<algorithm>/seed_<n>/device_metrics.csv`
- `outputs/experiments/<scenario>/<algorithm>/seed_<n>/slice_summary.csv`
- `outputs/experiments/<scenario>/<algorithm>/seed_<n>/run_metadata.json`

Key summary metrics include:

- p95/p99 latency per slice
- SLA violation count and rate
- Jain fairness index
- Utility score

## Day 2 Research Pipeline (PSDAS + Ablations)

Run static, dynamic, and PSDAS together:

```bash
python3 run_experiments.py --seed-count 10 --algorithms static dynamic psdas
```

Run PSDAS ablations (example: no prediction):

```bash
python3 run_experiments.py --algorithms psdas --seed-count 10 --psdas-no-prediction
```

Other ablation flags:

- `--psdas-no-debt`
- `--psdas-fixed-weights`

## Extension Ideas for Research

- Add reinforcement learning or optimization-based slice allocation
- Add mobility and handover simulation
- Add variable radio channel quality models
- Add SLA violation scoring for each service class
- Add energy-efficiency and fairness metrics
