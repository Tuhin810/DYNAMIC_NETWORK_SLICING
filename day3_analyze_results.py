from __future__ import annotations

import argparse
import csv
import math
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PRIMARY_METRICS = [
    (
        "overall_sla_violation_rate_pct",
        "Overall SLA Violation Rate (%)",
        "lower",
    ),
    (
        "utility_score",
        "Utility Score",
        "higher",
    ),
    (
        "urllc_p95_latency_ms",
        "URLLC p95 Latency (ms)",
        "lower",
    ),
    (
        "embb_avg_throughput_mbps",
        "eMBB Avg Throughput (Mbps)",
        "higher",
    ),
]

ABLATION_VARIANTS = [
    "psdas",
    "psdas_no_prediction",
    "psdas_no_debt",
    "psdas_fixed_weights",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Day 3 research analysis: stats, significance, and paper-ready figures."
    )
    parser.add_argument(
        "--base-summary-csv",
        type=str,
        required=True,
        help="runs_summary.csv containing static, dynamic, and psdas runs.",
    )
    parser.add_argument(
        "--base-output-dir",
        type=str,
        required=True,
        help="Output directory used for base runs (contains per-seed device_metrics.csv).",
    )
    parser.add_argument(
        "--ablation-summary-csvs",
        nargs="*",
        default=[],
        help="Optional list of ablation runs_summary.csv files.",
    )
    parser.add_argument(
        "--paper-figures-dir",
        type=str,
        default="outputs/paper_figures",
        help="Directory where paper-quality figures are saved.",
    )
    parser.add_argument(
        "--report-dir",
        type=str,
        default="outputs/day3_report",
        help="Directory where markdown/csv analysis artifacts are saved.",
    )
    parser.add_argument(
        "--permutation-iterations",
        type=int,
        default=20000,
        help="Number of iterations for paired permutation p-values.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260422,
        help="Random seed for permutation tests.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    base_summary_path = Path(args.base_summary_csv)
    base_output_dir = Path(args.base_output_dir)
    report_dir = Path(args.report_dir)
    figures_dir = Path(args.paper_figures_dir)

    report_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    base_rows = _load_summary_rows(base_summary_path)
    ablation_rows = []
    for ablation_summary_csv in args.ablation_summary_csvs:
        ablation_rows.extend(_load_summary_rows(Path(ablation_summary_csv)))

    all_rows = list(base_rows) + list(ablation_rows)

    aggregate_rows = _build_aggregate_rows(rows=all_rows)
    _write_csv(report_dir / "aggregate_metrics.csv", aggregate_rows)

    significance_rows = _build_psdas_vs_dynamic_rows(
        rows=base_rows,
        permutation_iterations=args.permutation_iterations,
        permutation_seed=args.seed,
    )
    _write_csv(report_dir / "psdas_vs_dynamic_stats.csv", significance_rows)
    _write_significance_markdown(
        output_file=report_dir / "psdas_vs_dynamic_stats.md",
        rows=significance_rows,
    )

    ablation_summary_rows = _build_ablation_rows(rows=all_rows)
    _write_csv(report_dir / "ablation_impact.csv", ablation_summary_rows)
    _write_ablation_markdown(
        output_file=report_dir / "ablation_impact.md",
        rows=ablation_summary_rows,
    )

    _plot_metric_ci(
        rows=base_rows,
        metric_key="overall_sla_violation_rate_pct",
        metric_title="Overall SLA Violation Rate (%)",
        output_file=figures_dir / "fig1_sla_violation_ci.png",
    )
    _plot_metric_ci(
        rows=base_rows,
        metric_key="utility_score",
        metric_title="Utility Score",
        output_file=figures_dir / "fig2_utility_ci.png",
    )
    _plot_metric_ci(
        rows=base_rows,
        metric_key="urllc_p95_latency_ms",
        metric_title="URLLC p95 Latency (ms)",
        output_file=figures_dir / "fig3_urllc_p95_ci.png",
    )

    cdf_latency = _load_latency_for_cdf(base_output_dir=base_output_dir)
    _plot_latency_cdf(
        latency_by_slice_and_algorithm=cdf_latency,
        output_file=figures_dir / "fig4_latency_cdf_per_slice.png",
    )

    _plot_ablation_impact(
        rows=all_rows,
        metric_key="utility_score",
        metric_title="Ablation Study: Utility Score",
        output_file=figures_dir / "fig5_ablation_utility.png",
    )
    _plot_ablation_impact(
        rows=all_rows,
        metric_key="overall_sla_violation_rate_pct",
        metric_title="Ablation Study: SLA Violation Rate (%)",
        output_file=figures_dir / "fig6_ablation_sla_violation.png",
    )

    findings = _build_findings_summary(
        significance_rows=significance_rows,
        ablation_rows=ablation_summary_rows,
    )
    (report_dir / "day3_findings_summary.md").write_text(findings, encoding="utf-8")

    print("Day 3 analysis complete.")
    print(f"- Report directory: {report_dir}")
    print(f"- Figures directory: {figures_dir}")


def _load_summary_rows(file_path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    with file_path.open("r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for raw in reader:
            row: dict[str, object] = {
                "scenario": raw["scenario"],
                "algorithm": raw["algorithm"],
                "seed": int(raw["seed"]),
            }
            for key, value in raw.items():
                if key in {"scenario", "algorithm"}:
                    continue
                if key == "seed":
                    continue
                try:
                    row[key] = float(value)
                except ValueError:
                    row[key] = value
            rows.append(row)

    return rows


def _build_aggregate_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["scenario"]), str(row["algorithm"]))].append(row)

    out_rows: list[dict[str, object]] = []
    for scenario, algorithm in sorted(grouped.keys()):
        items = grouped[(scenario, algorithm)]
        for metric_key, metric_title, _ in PRIMARY_METRICS:
            values = [float(item[metric_key]) for item in items]
            metric_mean = _mean(values)
            ci = _ci95(values)
            out_rows.append(
                {
                    "scenario": scenario,
                    "algorithm": algorithm,
                    "metric_key": metric_key,
                    "metric_title": metric_title,
                    "n": len(values),
                    "mean": round(metric_mean, 6),
                    "std": round(_std(values), 6),
                    "ci95_low": round(metric_mean - ci, 6),
                    "ci95_high": round(metric_mean + ci, 6),
                }
            )

    return out_rows


def _build_psdas_vs_dynamic_rows(
    rows: list[dict[str, object]],
    permutation_iterations: int,
    permutation_seed: int,
) -> list[dict[str, object]]:
    scenarios = sorted({str(row["scenario"]) for row in rows})
    out_rows: list[dict[str, object]] = []

    rows_by_key: dict[tuple[str, str], dict[int, dict[str, object]]] = defaultdict(dict)
    for row in rows:
        rows_by_key[(str(row["scenario"]), str(row["algorithm"]))][int(row["seed"])] = row

    for scenario in scenarios:
        dynamic_runs = rows_by_key.get((scenario, "dynamic"), {})
        psdas_runs = rows_by_key.get((scenario, "psdas"), {})

        common_seeds = sorted(set(dynamic_runs.keys()) & set(psdas_runs.keys()))
        if not common_seeds:
            continue

        for metric_key, metric_title, direction in PRIMARY_METRICS:
            dynamic_values = [float(dynamic_runs[seed][metric_key]) for seed in common_seeds]
            psdas_values = [float(psdas_runs[seed][metric_key]) for seed in common_seeds]
            diffs = [psdas - dynamic for psdas, dynamic in zip(psdas_values, dynamic_values)]

            observed_delta = _mean(diffs)
            p_value = _paired_permutation_p_value(
                diffs=diffs,
                iterations=permutation_iterations,
                rng=random.Random(permutation_seed + hash((scenario, metric_key)) % 10_000_000),
            )
            effect_size = _cohen_dz(diffs)
            dynamic_mean = _mean(dynamic_values)
            psdas_mean = _mean(psdas_values)

            if direction == "lower":
                better = "psdas" if observed_delta < 0 else "dynamic"
                improvement_pct = (
                    0.0 if dynamic_mean == 0 else ((dynamic_mean - psdas_mean) / dynamic_mean) * 100.0
                )
            else:
                better = "psdas" if observed_delta > 0 else "dynamic"
                improvement_pct = (
                    0.0 if dynamic_mean == 0 else ((psdas_mean - dynamic_mean) / dynamic_mean) * 100.0
                )

            out_rows.append(
                {
                    "scenario": scenario,
                    "metric_key": metric_key,
                    "metric_title": metric_title,
                    "n_paired": len(common_seeds),
                    "dynamic_mean": round(dynamic_mean, 6),
                    "psdas_mean": round(psdas_mean, 6),
                    "psdas_minus_dynamic": round(observed_delta, 6),
                    "improvement_pct": round(improvement_pct, 4),
                    "p_value": round(p_value, 6),
                    "effect_size_dz": round(effect_size, 6),
                    "better_algorithm": better,
                    "statistically_significant_0_05": p_value < 0.05,
                    "p_value_holm": 1.0,
                    "statistically_significant_holm_0_05": False,
                }
            )

    _apply_holm_bonferroni(
        rows=out_rows,
        p_value_key="p_value",
        adjusted_key="p_value_holm",
    )
    for row in out_rows:
        row["statistically_significant_holm_0_05"] = float(row["p_value_holm"]) < 0.05

    return out_rows


def _build_ablation_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["scenario"]), str(row["algorithm"]))].append(row)

    scenarios = sorted({str(row["scenario"]) for row in rows})
    out_rows: list[dict[str, object]] = []

    for scenario in scenarios:
        for metric_key, metric_title, direction in PRIMARY_METRICS:
            baseline_values = [
                float(item[metric_key]) for item in grouped.get((scenario, "psdas"), [])
            ]
            if not baseline_values:
                continue
            baseline_mean = _mean(baseline_values)

            for variant in ABLATION_VARIANTS:
                values = [float(item[metric_key]) for item in grouped.get((scenario, variant), [])]
                if not values:
                    continue
                variant_mean = _mean(values)

                if direction == "lower":
                    delta_vs_psdas = variant_mean - baseline_mean
                    relative_pct = 0.0 if baseline_mean == 0 else (delta_vs_psdas / baseline_mean) * 100.0
                else:
                    delta_vs_psdas = baseline_mean - variant_mean
                    relative_pct = 0.0 if baseline_mean == 0 else (delta_vs_psdas / baseline_mean) * 100.0

                out_rows.append(
                    {
                        "scenario": scenario,
                        "variant": variant,
                        "metric_key": metric_key,
                        "metric_title": metric_title,
                        "mean": round(variant_mean, 6),
                        "delta_from_psdas_directional": round(delta_vs_psdas, 6),
                        "degradation_pct_vs_psdas": round(relative_pct, 4),
                    }
                )

    return out_rows


def _plot_metric_ci(
    rows: list[dict[str, object]],
    metric_key: str,
    metric_title: str,
    output_file: Path,
) -> None:
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[str(row["scenario"])][str(row["algorithm"])].append(float(row[metric_key]))

    scenarios = sorted(grouped.keys())
    algorithms = ["static", "dynamic", "psdas"]

    x_positions = list(range(len(scenarios)))
    width = 0.24
    colors = {"static": "#355C7D", "dynamic": "#F67280", "psdas": "#2A9D8F"}

    fig, ax = plt.subplots(figsize=(12.0, 6.0))

    for idx, algorithm in enumerate(algorithms):
        offset = (idx - (len(algorithms) - 1) / 2) * width
        means: list[float] = []
        ci95s: list[float] = []

        for scenario in scenarios:
            values = grouped[scenario].get(algorithm, [])
            means.append(_mean(values))
            ci95s.append(_ci95(values))

        positions = [position + offset for position in x_positions]
        ax.bar(
            positions,
            means,
            width=width,
            yerr=ci95s,
            capsize=4,
            label=algorithm,
            color=colors.get(algorithm, "#666666"),
            alpha=0.92,
        )

    ax.set_title(f"{metric_title} Across Scenarios (mean +/- 95% CI)")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(scenarios)
    ax.set_ylabel(metric_title)
    ax.grid(axis="y", linestyle="--", alpha=0.30)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_file, dpi=220)
    plt.close(fig)


def _load_latency_for_cdf(base_output_dir: Path) -> dict[str, dict[str, list[float]]]:
    latency_by_slice_and_algorithm: dict[str, dict[str, list[float]]] = {
        "mMTC": {"static": [], "dynamic": [], "psdas": []},
        "eMBB": {"static": [], "dynamic": [], "psdas": []},
        "URLLC": {"static": [], "dynamic": [], "psdas": []},
    }

    if not base_output_dir.exists():
        return latency_by_slice_and_algorithm

    for scenario_dir in sorted(path for path in base_output_dir.iterdir() if path.is_dir()):
        for algorithm in ["static", "dynamic", "psdas"]:
            algorithm_dir = scenario_dir / algorithm
            if not algorithm_dir.exists():
                continue

            seed_dirs = sorted(path for path in algorithm_dir.iterdir() if path.is_dir())
            for seed_dir in seed_dirs:
                metrics_file = seed_dir / "device_metrics.csv"
                if not metrics_file.exists():
                    continue
                with metrics_file.open("r", encoding="utf-8") as csv_file:
                    reader = csv.DictReader(csv_file)
                    for row in reader:
                        slice_name = row["slice_name"]
                        latency_ms = float(row["latency_ms"])
                        if slice_name in latency_by_slice_and_algorithm:
                            latency_by_slice_and_algorithm[slice_name][algorithm].append(latency_ms)

    return latency_by_slice_and_algorithm


def _plot_latency_cdf(
    latency_by_slice_and_algorithm: dict[str, dict[str, list[float]]],
    output_file: Path,
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16.5, 4.8), sharey=True)
    colors = {"static": "#355C7D", "dynamic": "#F67280", "psdas": "#2A9D8F"}

    for axis, slice_name in zip(axes, ["mMTC", "eMBB", "URLLC"]):
        for algorithm in ["static", "dynamic", "psdas"]:
            values = sorted(latency_by_slice_and_algorithm[slice_name][algorithm])
            if not values:
                continue
            ranks = [index / len(values) for index in range(1, len(values) + 1)]
            axis.plot(values, ranks, label=algorithm, linewidth=1.8, color=colors[algorithm])

        axis.set_title(f"{slice_name} Latency CDF")
        axis.set_xlabel("Latency (ms)")
        axis.grid(True, linestyle="--", alpha=0.25)

    axes[0].set_ylabel("CDF")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.05))
    fig.tight_layout()
    fig.savefig(output_file, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _plot_ablation_impact(
    rows: list[dict[str, object]],
    metric_key: str,
    metric_title: str,
    output_file: Path,
) -> None:
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        algorithm = str(row["algorithm"])
        if algorithm not in ABLATION_VARIANTS:
            continue
        scenario = str(row["scenario"])
        grouped[scenario][algorithm].append(float(row[metric_key]))

    scenarios = sorted(grouped.keys())
    variants = ABLATION_VARIANTS

    x_positions = list(range(len(scenarios)))
    width = 0.18
    color_map = {
        "psdas": "#2A9D8F",
        "psdas_no_prediction": "#264653",
        "psdas_no_debt": "#E76F51",
        "psdas_fixed_weights": "#E9C46A",
    }

    fig, ax = plt.subplots(figsize=(13.5, 6.0))
    for idx, variant in enumerate(variants):
        offset = (idx - (len(variants) - 1) / 2) * width
        means: list[float] = []
        ci95s: list[float] = []

        for scenario in scenarios:
            values = grouped[scenario].get(variant, [])
            means.append(_mean(values))
            ci95s.append(_ci95(values))

        positions = [position + offset for position in x_positions]
        ax.bar(
            positions,
            means,
            width=width,
            yerr=ci95s,
            capsize=3,
            label=variant,
            color=color_map.get(variant, "#999999"),
            alpha=0.92,
        )

    ax.set_title(f"{metric_title} by PSDAS Variant (mean +/- 95% CI)")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(scenarios)
    ax.set_ylabel(metric_title)
    ax.grid(axis="y", linestyle="--", alpha=0.30)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_file, dpi=220)
    plt.close(fig)


def _write_significance_markdown(output_file: Path, rows: list[dict[str, object]]) -> None:
    lines = [
        "# PSDAS vs Dynamic: Statistical Comparison",
        "",
        "Paired permutation test, two-sided p-value, with Holm-Bonferroni correction across all listed comparisons.",
        "",
        "| Scenario | Metric | Dynamic Mean | PSDAS Mean | Delta (P-D) | Improvement (%) | p-value | p-value (Holm) | dz | Better | Significant (raw) | Significant (Holm) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]

    for row in rows:
        lines.append(
            "| "
            f"{row['scenario']} | {row['metric_title']} | {row['dynamic_mean']:.4f} | "
            f"{row['psdas_mean']:.4f} | {row['psdas_minus_dynamic']:+.4f} | "
            f"{row['improvement_pct']:+.2f} | {row['p_value']:.4f} | "
            f"{row['p_value_holm']:.4f} | {row['effect_size_dz']:+.3f} | {row['better_algorithm']} | "
            f"{str(row['statistically_significant_0_05'])} | "
            f"{str(row['statistically_significant_holm_0_05'])} |"
        )

    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_ablation_markdown(output_file: Path, rows: list[dict[str, object]]) -> None:
    lines = [
        "# PSDAS Ablation Impact",
        "",
        "Directional degradation is measured relative to full PSDAS (positive means ablation hurts PSDAS).",
        "",
        "| Scenario | Variant | Metric | Mean | Directional Degradation | Degradation (%) |",
        "|---|---|---|---:|---:|---:|",
    ]

    for row in rows:
        lines.append(
            "| "
            f"{row['scenario']} | {row['variant']} | {row['metric_title']} | {row['mean']:.4f} | "
            f"{row['delta_from_psdas_directional']:+.4f} | {row['degradation_pct_vs_psdas']:+.2f} |"
        )

    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_findings_summary(
    significance_rows: list[dict[str, object]],
    ablation_rows: list[dict[str, object]],
) -> str:
    scenario_win_counter_raw: dict[str, int] = defaultdict(int)
    scenario_win_counter_holm: dict[str, int] = defaultdict(int)
    scenario_metric_counter: dict[str, int] = defaultdict(int)

    for row in significance_rows:
        scenario = str(row["scenario"])
        scenario_metric_counter[scenario] += 1
        if bool(row["statistically_significant_0_05"]) and str(row["better_algorithm"]) == "psdas":
            scenario_win_counter_raw[scenario] += 1
        if bool(row["statistically_significant_holm_0_05"]) and str(row["better_algorithm"]) == "psdas":
            scenario_win_counter_holm[scenario] += 1

    lines = [
        "# Day 3 Findings Summary",
        "",
        "## Statistical Outcome",
    ]

    for scenario in sorted(scenario_metric_counter.keys()):
        wins_raw = scenario_win_counter_raw[scenario]
        wins_holm = scenario_win_counter_holm[scenario]
        total = scenario_metric_counter[scenario]
        lines.append(
            f"- {scenario}: PSDAS significant wins in {wins_raw}/{total} metrics (raw p < 0.05) and {wins_holm}/{total} metrics (Holm-adjusted p < 0.05)."
        )

    lines.extend(
        [
            "",
            "## Failure Cases and Limits",
            "- Cases where dynamic wins or Holm-adjusted p-value >= 0.05 should be discussed as workload-specific limits.",
            "- Effect sizes close to zero indicate practical parity even when means differ.",
            "- Use ablation degradations to support that prediction/debt/weights each contribute to final gains.",
            "",
            "## Figure Interpretation Notes",
            "- Figure 1: SLA violation CI bars quantify robustness under stress scenarios.",
            "- Figure 2: Utility CI bars summarize multi-objective quality gains.",
            "- Figure 3: URLLC p95 CI bars test tail-latency sensitivity.",
            "- Figure 4: Per-slice latency CDFs reveal distributional shifts, not only mean shifts.",
            "- Figure 5-6: Ablation plots show contribution of prediction, debt, and adaptive weighting.",
        ]
    )

    if ablation_rows:
        worst = sorted(
            ablation_rows,
            key=lambda row: float(row["degradation_pct_vs_psdas"]),
            reverse=True,
        )[:5]
        lines.append("")
        lines.append("## Largest Ablation Degradations")
        for row in worst:
            lines.append(
                "- "
                f"{row['scenario']} | {row['variant']} | {row['metric_title']} | "
                f"{row['degradation_pct_vs_psdas']:+.2f}%"
            )

    return "\n".join(lines) + "\n"


def _apply_holm_bonferroni(
    rows: list[dict[str, object]],
    p_value_key: str,
    adjusted_key: str,
) -> None:
    if not rows:
        return

    ranked = sorted(
        enumerate(rows),
        key=lambda item: float(item[1][p_value_key]),
    )
    total_tests = len(ranked)
    adjusted: list[float] = [1.0 for _ in rows]
    running_max = 0.0

    for rank, (original_index, row) in enumerate(ranked):
        raw_p = float(row[p_value_key])
        multiplier = total_tests - rank
        corrected = min(1.0, raw_p * multiplier)
        running_max = max(running_max, corrected)
        adjusted[original_index] = running_max

    for index, row in enumerate(rows):
        row[adjusted_key] = round(adjusted[index], 6)


def _write_csv(file_path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return

    fieldnames = list(rows[0].keys())
    with file_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _paired_permutation_p_value(diffs: list[float], iterations: int, rng: random.Random) -> float:
    if not diffs:
        return 1.0

    observed = abs(_mean(diffs))
    extreme = 0

    for _ in range(iterations):
        signed = [value if rng.random() < 0.5 else -value for value in diffs]
        if abs(_mean(signed)) >= observed:
            extreme += 1

    return (extreme + 1) / (iterations + 1)


def _cohen_dz(diffs: list[float]) -> float:
    if len(diffs) < 2:
        return 0.0

    sigma = _std(diffs)
    if sigma == 0.0:
        return 0.0
    return _mean(diffs) / sigma


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return mean(values)


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return stdev(values)


def _ci95(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return 1.96 * (_std(values) / math.sqrt(len(values)))


if __name__ == "__main__":
    main()
