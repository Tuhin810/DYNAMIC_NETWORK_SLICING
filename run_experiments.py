from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path
from statistics import mean

from scenarios import (
    ExperimentRunConfig,
    generate_devices_for_scenario,
    get_scenario_preset,
    list_scenario_names,
)
from simulation import SimulationResult, simulate_network_performance
from slicing import SLICES, assign_dynamic_slices, assign_static_slices


def parse_args() -> argparse.Namespace:
    """Parses CLI options for batch experiment execution."""
    parser = argparse.ArgumentParser(description="Batch experiment runner for slicing policies.")
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=["balanced", "video_heavy", "emergency_burst"],
        help="Scenario names or 'all'.",
    )
    parser.add_argument(
        "--algorithms",
        nargs="+",
        choices=["static", "dynamic"],
        default=["static", "dynamic"],
        help="Algorithms to evaluate.",
    )
    parser.add_argument(
        "--seed-start",
        type=int,
        default=1,
        help="First random seed for the run range.",
    )
    parser.add_argument(
        "--seed-count",
        type=int,
        default=10,
        help="How many seeds to evaluate per scenario and algorithm.",
    )
    parser.add_argument(
        "--devices",
        type=int,
        default=None,
        help="Override scenario default number of devices (minimum 100).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/experiments",
        help="Directory for all experiment artifacts.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    selected_scenarios = _resolve_scenarios(args.scenarios)
    seeds = list(range(args.seed_start, args.seed_start + args.seed_count))
    output_root = Path(args.output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    run_rows: list[dict[str, object]] = []

    for scenario_name in selected_scenarios:
        scenario = get_scenario_preset(scenario_name)

        for algorithm in args.algorithms:
            for seed in seeds:
                num_devices = scenario.num_devices if args.devices is None else args.devices
                if num_devices < 100:
                    raise ValueError("--devices must be at least 100")

                config = ExperimentRunConfig(
                    scenario_name=scenario.name,
                    algorithm=algorithm,
                    num_devices=num_devices,
                    seed=seed,
                    device_mix=scenario.device_mix,
                    background_load=scenario.background_load,
                )

                devices = generate_devices_for_scenario(
                    scenario=scenario,
                    seed=seed,
                    num_devices=num_devices,
                )

                if algorithm == "static":
                    assignments = assign_static_slices(devices)
                else:
                    assignments = assign_dynamic_slices(
                        devices=devices,
                        background_load=scenario.background_load,
                    )

                result = simulate_network_performance(
                    devices=devices,
                    assignments=assignments,
                    mode=algorithm,
                    seed=seed + 500,
                    background_load=scenario.background_load,
                )

                run_dir = output_root / scenario.name / algorithm / f"seed_{seed}"
                _export_run_artifacts(
                    run_dir=run_dir,
                    config=config,
                    scenario_description=scenario.description,
                    result=result,
                )
                run_rows.append(_flatten_run_row(config=config, result=result))

    _write_runs_summary_csv(output_root=output_root, run_rows=run_rows)
    _write_baseline_markdown(output_root=output_root, run_rows=run_rows)

    print(
        "Completed experiments: "
        f"{len(run_rows)} runs across {len(selected_scenarios)} scenarios. "
        f"Artifacts saved to {output_root}"
    )


def _resolve_scenarios(requested: list[str]) -> list[str]:
    """Resolves scenario selection from explicit names or 'all'."""
    if any(item.lower() == "all" for item in requested):
        return list_scenario_names()
    return requested


def _export_run_artifacts(
    run_dir: Path,
    config: ExperimentRunConfig,
    scenario_description: str,
    result: SimulationResult,
) -> None:
    """Writes per-run CSV and JSON artifacts required for reproducibility."""
    run_dir.mkdir(parents=True, exist_ok=True)

    _write_device_metrics_csv(file_path=run_dir / "device_metrics.csv", result=result)
    _write_slice_summary_csv(file_path=run_dir / "slice_summary.csv", result=result)

    metadata = {
        "run_config": config.as_dict(),
        "scenario_description": scenario_description,
        "overall_metrics": {
            "overall_sla_violation_count": result.overall_sla_violation_count,
            "overall_sla_violation_rate_pct": result.overall_sla_violation_rate_pct,
            "fairness_index": result.fairness_index,
            "utility_score": result.utility_score,
        },
        "slice_summary": {
            slice_name: asdict(summary) for slice_name, summary in result.slice_summary.items()
        },
    }

    with (run_dir / "run_metadata.json").open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, indent=2)


def _write_device_metrics_csv(file_path: Path, result: SimulationResult) -> None:
    """Exports per-device simulation output as CSV."""
    with file_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "mode",
                "device_id",
                "slice_name",
                "latency_ms",
                "throughput_mbps",
                "packet_loss_pct",
            ],
        )
        writer.writeheader()

        for record in result.device_metrics:
            writer.writerow(
                {
                    "mode": result.mode,
                    "device_id": record.device_id,
                    "slice_name": record.slice_name,
                    "latency_ms": record.latency_ms,
                    "throughput_mbps": record.throughput_mbps,
                    "packet_loss_pct": record.packet_loss_pct,
                }
            )


def _write_slice_summary_csv(file_path: Path, result: SimulationResult) -> None:
    """Exports per-slice summary statistics as CSV."""
    with file_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "mode",
                "slice_name",
                "device_count",
                "avg_latency_ms",
                "p95_latency_ms",
                "p99_latency_ms",
                "avg_throughput_mbps",
                "avg_packet_loss_pct",
                "sla_violation_count",
                "sla_violation_rate_pct",
                "load_ratio",
            ],
        )
        writer.writeheader()

        for slice_name in SLICES:
            summary = result.slice_summary[slice_name]
            writer.writerow(
                {
                    "mode": result.mode,
                    "slice_name": slice_name,
                    "device_count": summary.device_count,
                    "avg_latency_ms": summary.avg_latency_ms,
                    "p95_latency_ms": summary.p95_latency_ms,
                    "p99_latency_ms": summary.p99_latency_ms,
                    "avg_throughput_mbps": summary.avg_throughput_mbps,
                    "avg_packet_loss_pct": summary.avg_packet_loss_pct,
                    "sla_violation_count": summary.sla_violation_count,
                    "sla_violation_rate_pct": summary.sla_violation_rate_pct,
                    "load_ratio": summary.load_ratio,
                }
            )


def _flatten_run_row(config: ExperimentRunConfig, result: SimulationResult) -> dict[str, object]:
    """Builds a flat run row for global summary aggregation."""
    row: dict[str, object] = {
        "scenario": config.scenario_name,
        "algorithm": config.algorithm,
        "seed": config.seed,
        "num_devices": config.num_devices,
        "overall_sla_violation_count": result.overall_sla_violation_count,
        "overall_sla_violation_rate_pct": result.overall_sla_violation_rate_pct,
        "fairness_index": result.fairness_index,
        "utility_score": result.utility_score,
    }

    for slice_name in SLICES:
        summary = result.slice_summary[slice_name]
        prefix = slice_name.lower()
        row[f"{prefix}_avg_latency_ms"] = summary.avg_latency_ms
        row[f"{prefix}_p95_latency_ms"] = summary.p95_latency_ms
        row[f"{prefix}_p99_latency_ms"] = summary.p99_latency_ms
        row[f"{prefix}_avg_throughput_mbps"] = summary.avg_throughput_mbps
        row[f"{prefix}_avg_packet_loss_pct"] = summary.avg_packet_loss_pct
        row[f"{prefix}_sla_violation_rate_pct"] = summary.sla_violation_rate_pct
        row[f"{prefix}_load_ratio"] = summary.load_ratio

    return row


def _write_runs_summary_csv(output_root: Path, run_rows: list[dict[str, object]]) -> None:
    """Writes global run summary CSV with one row per scenario-algorithm-seed run."""
    if not run_rows:
        return

    fieldnames = list(run_rows[0].keys())
    summary_path = output_root / "runs_summary.csv"

    with summary_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(run_rows)


def _write_baseline_markdown(output_root: Path, run_rows: list[dict[str, object]]) -> None:
    """Creates a quick baseline comparison markdown table for paper drafting."""
    if not run_rows:
        return

    grouped: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in run_rows:
        key = (str(row["scenario"]), str(row["algorithm"]))
        grouped.setdefault(key, []).append(row)

    lines = [
        "# Baseline Comparison (Day 1)",
        "",
        "| Scenario | Algorithm | SLA Violation (%) | Fairness | Utility | URLLC p95 Latency (ms) |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    ordered_keys = sorted(grouped.keys(), key=lambda item: (item[0], item[1]))
    for scenario, algorithm in ordered_keys:
        rows = grouped[(scenario, algorithm)]
        sla = mean(float(item["overall_sla_violation_rate_pct"]) for item in rows)
        fairness = mean(float(item["fairness_index"]) for item in rows)
        utility = mean(float(item["utility_score"]) for item in rows)
        urllc_p95 = mean(float(item["urllc_p95_latency_ms"]) for item in rows)
        lines.append(
            f"| {scenario} | {algorithm} | {sla:.3f} | {fairness:.4f} | {utility:.4f} | {urllc_p95:.3f} |"
        )

    baseline_path = output_root / "baseline_comparison.md"
    baseline_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()