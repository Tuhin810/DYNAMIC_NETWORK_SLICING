from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


METRICS = [
    (
        "overall_sla_violation_rate_pct",
        "Overall SLA Violation Rate (%)",
        "Lower is better",
    ),
    (
        "utility_score",
        "Utility Score",
        "Higher is better",
    ),
    (
        "fairness_index",
        "Jain Fairness Index",
        "Higher is better",
    ),
    (
        "urllc_p95_latency_ms",
        "URLLC p95 Latency (ms)",
        "Lower is better",
    ),
    (
        "embb_avg_throughput_mbps",
        "eMBB Avg Throughput (Mbps)",
        "Higher is better",
    ),
]


def parse_args() -> argparse.Namespace:
    """Parses command line arguments for plotting experiment outputs."""
    parser = argparse.ArgumentParser(description="Generate plots from experiment summary CSV.")
    parser.add_argument(
        "--summary-csv",
        type=str,
        default="outputs/experiments_rerun_30/runs_summary.csv",
        help="Path to runs_summary.csv produced by run_experiments.py.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/experiments_rerun_30/plots",
        help="Directory to store generated graph images.",
    )
    parser.add_argument(
        "--previous-summary-csv",
        type=str,
        default=None,
        help="Optional previous runs_summary.csv to generate old-vs-new delta plots.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    summary_path = Path(args.summary_csv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    current_rows = _load_rows(summary_path)
    previous_rows: list[dict[str, object]] | None = None

    generated_files: list[Path] = []
    for metric_key, metric_title, better_note in METRICS:
        file_path = output_dir / f"{metric_key}_comparison.png"
        _plot_metric_with_ci(
            rows=current_rows,
            metric_key=metric_key,
            metric_title=metric_title,
            subtitle=better_note,
            output_file=file_path,
        )
        generated_files.append(file_path)

    if args.previous_summary_csv:
        previous_path = Path(args.previous_summary_csv)
        previous_rows = _load_rows(previous_path)

        for metric_key, metric_title, better_note in METRICS:
            file_path = output_dir / f"delta_{metric_key}.png"
            _plot_delta_vs_previous(
                previous_rows=previous_rows,
                current_rows=current_rows,
                metric_key=metric_key,
                metric_title=metric_title,
                subtitle=better_note,
                output_file=file_path,
            )
            generated_files.append(file_path)

    dashboard_file = output_dir / "paper_dashboard.png"
    _plot_paper_dashboard(
        rows=current_rows,
        output_file=dashboard_file,
    )
    generated_files.append(dashboard_file)

    if previous_rows is not None:
        delta_dashboard_file = output_dir / "paper_delta_dashboard.png"
        _plot_delta_dashboard(
            previous_rows=previous_rows,
            current_rows=current_rows,
            output_file=delta_dashboard_file,
        )
        generated_files.append(delta_dashboard_file)

    print("Generated graph files:")
    for file_path in generated_files:
        print(f"- {file_path}")


def _load_rows(file_path: Path) -> list[dict[str, object]]:
    """Loads runs summary rows and converts known numeric fields."""
    rows: list[dict[str, object]] = []
    with file_path.open("r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            converted: dict[str, object] = {
                "scenario": row["scenario"],
                "algorithm": row["algorithm"],
            }
            for metric_key, _, _ in METRICS:
                converted[metric_key] = float(row[metric_key])
            rows.append(converted)
    return rows


def _plot_metric_with_ci(
    rows: list[dict[str, object]],
    metric_key: str,
    metric_title: str,
    subtitle: str,
    output_file: Path,
) -> None:
    """Creates grouped bar chart (by scenario and algorithm) with 95% CI."""
    grouped = _group_metric_values(rows=rows, metric_key=metric_key)
    scenarios = sorted(grouped.keys())
    algorithms = _ordered_algorithms(rows)

    x_positions = list(range(len(scenarios)))
    width = 0.35

    fig, ax = plt.subplots(figsize=(11, 5.8))
    colors = {"static": "#4C78A8", "dynamic": "#F58518"}

    for index, algorithm in enumerate(algorithms):
        offset = (index - (len(algorithms) - 1) / 2) * width
        means: list[float] = []
        ci95s: list[float] = []

        for scenario in scenarios:
            values = grouped[scenario].get(algorithm, [])
            means.append(_mean(values))
            ci95s.append(_ci95(values))

        positions = [x + offset for x in x_positions]
        bars = ax.bar(
            positions,
            means,
            width=width,
            yerr=ci95s,
            capsize=4,
            label=algorithm.capitalize(),
            color=colors.get(algorithm, "#72B7B2"),
            alpha=0.92,
        )

        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"{height:.3f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    ax.set_title(f"{metric_title}\n{subtitle}")
    ax.set_ylabel(metric_title)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(scenarios)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_file, dpi=170)
    plt.close(fig)


def _plot_delta_vs_previous(
    previous_rows: list[dict[str, object]],
    current_rows: list[dict[str, object]],
    metric_key: str,
    metric_title: str,
    subtitle: str,
    output_file: Path,
) -> None:
    """Plots current-minus-previous mean deltas by scenario and algorithm."""
    previous_grouped = _group_metric_values(rows=previous_rows, metric_key=metric_key)
    current_grouped = _group_metric_values(rows=current_rows, metric_key=metric_key)

    scenarios = sorted(current_grouped.keys())
    algorithms = _ordered_algorithms(current_rows)

    labels: list[str] = []
    deltas: list[float] = []
    colors: list[str] = []

    for scenario in scenarios:
        for algorithm in algorithms:
            prev_values = previous_grouped.get(scenario, {}).get(algorithm, [])
            curr_values = current_grouped.get(scenario, {}).get(algorithm, [])
            if not prev_values or not curr_values:
                continue

            delta = _mean(curr_values) - _mean(prev_values)
            labels.append(f"{scenario}\n{algorithm}")
            deltas.append(delta)
            colors.append("#4CAF50" if delta <= 0 else "#D32F2F")

    fig, ax = plt.subplots(figsize=(12.5, 5.8))
    x_positions = list(range(len(labels)))
    bars = ax.bar(x_positions, deltas, color=colors, alpha=0.9)
    ax.axhline(0.0, color="black", linewidth=1)

    for bar, delta in zip(bars, deltas):
        ax.annotate(
            f"{delta:+.3f}",
            xy=(bar.get_x() + bar.get_width() / 2, delta),
            xytext=(0, 3 if delta >= 0 else -13),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    ax.set_title(f"Delta vs Previous ({metric_title})\nCurrent - Previous, {subtitle}")
    ax.set_ylabel("Delta")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(output_file, dpi=170)
    plt.close(fig)


def _plot_paper_dashboard(
    rows: list[dict[str, object]],
    output_file: Path,
) -> None:
    """Creates a single multi-panel dashboard for key comparison metrics."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 10.5))
    axes_flat = [ax for row in axes for ax in row]

    for index, (metric_key, metric_title, better_note) in enumerate(METRICS):
        ax = axes_flat[index]
        _draw_metric_panel(
            ax=ax,
            rows=rows,
            metric_key=metric_key,
            metric_title=metric_title,
            subtitle=better_note,
            annotate=False,
        )

    insight_ax = axes_flat[-1]
    insight_ax.axis("off")
    insight_text = _build_dashboard_insight_text(rows)
    insight_ax.text(
        0.02,
        0.98,
        insight_text,
        va="top",
        ha="left",
        fontsize=11,
        family="monospace",
    )

    fig.suptitle("5G Slicing Baseline Dashboard (Current Runs)", fontsize=16, y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(output_file, dpi=190)
    plt.close(fig)


def _plot_delta_dashboard(
    previous_rows: list[dict[str, object]],
    current_rows: list[dict[str, object]],
    output_file: Path,
) -> None:
    """Creates a single dashboard image for current-vs-previous metric deltas."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 10.5))
    axes_flat = [ax for row in axes for ax in row]

    for index, (metric_key, metric_title, better_note) in enumerate(METRICS):
        ax = axes_flat[index]
        _draw_delta_panel(
            ax=ax,
            previous_rows=previous_rows,
            current_rows=current_rows,
            metric_key=metric_key,
            metric_title=metric_title,
            subtitle=better_note,
        )

    insight_ax = axes_flat[-1]
    insight_ax.axis("off")
    insight_text = _build_delta_insight_text(previous_rows=previous_rows, current_rows=current_rows)
    insight_ax.text(
        0.02,
        0.98,
        insight_text,
        va="top",
        ha="left",
        fontsize=11,
        family="monospace",
    )

    fig.suptitle("5G Slicing Delta Dashboard (Current - Previous)", fontsize=16, y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(output_file, dpi=190)
    plt.close(fig)


def _draw_metric_panel(
    ax: plt.Axes,
    rows: list[dict[str, object]],
    metric_key: str,
    metric_title: str,
    subtitle: str,
    annotate: bool,
) -> None:
    """Draws one grouped-bar metric panel with confidence intervals."""
    grouped = _group_metric_values(rows=rows, metric_key=metric_key)
    scenarios = sorted(grouped.keys())
    algorithms = _ordered_algorithms(rows)

    x_positions = list(range(len(scenarios)))
    width = 0.35
    colors = {"static": "#4C78A8", "dynamic": "#F58518"}

    for index, algorithm in enumerate(algorithms):
        offset = (index - (len(algorithms) - 1) / 2) * width
        means: list[float] = []
        ci95s: list[float] = []

        for scenario in scenarios:
            values = grouped[scenario].get(algorithm, [])
            means.append(_mean(values))
            ci95s.append(_ci95(values))

        positions = [x + offset for x in x_positions]
        bars = ax.bar(
            positions,
            means,
            width=width,
            yerr=ci95s,
            capsize=3,
            label=algorithm.capitalize(),
            color=colors.get(algorithm, "#72B7B2"),
            alpha=0.92,
        )

        if annotate:
            for bar in bars:
                height = bar.get_height()
                ax.annotate(
                    f"{height:.3f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

    ax.set_title(f"{metric_title}\n{subtitle}", fontsize=10)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(scenarios, fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    if metric_key == METRICS[0][0]:
        ax.legend(fontsize=8)


def _draw_delta_panel(
    ax: plt.Axes,
    previous_rows: list[dict[str, object]],
    current_rows: list[dict[str, object]],
    metric_key: str,
    metric_title: str,
    subtitle: str,
) -> None:
    """Draws one delta panel showing current-minus-previous means."""
    previous_grouped = _group_metric_values(rows=previous_rows, metric_key=metric_key)
    current_grouped = _group_metric_values(rows=current_rows, metric_key=metric_key)

    scenarios = sorted(current_grouped.keys())
    algorithms = _ordered_algorithms(current_rows)

    labels: list[str] = []
    deltas: list[float] = []
    colors: list[str] = []

    for scenario in scenarios:
        for algorithm in algorithms:
            prev_values = previous_grouped.get(scenario, {}).get(algorithm, [])
            curr_values = current_grouped.get(scenario, {}).get(algorithm, [])
            if not prev_values or not curr_values:
                continue

            delta = _mean(curr_values) - _mean(prev_values)
            labels.append(f"{scenario}\n{algorithm}")
            deltas.append(delta)
            colors.append("#2E7D32" if delta <= 0 else "#C62828")

    x_positions = list(range(len(labels)))
    ax.bar(x_positions, deltas, color=colors, alpha=0.9)
    ax.axhline(0.0, color="black", linewidth=1)
    ax.set_title(f"{metric_title}\nCurrent - Previous, {subtitle}", fontsize=10)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels, fontsize=7)
    ax.grid(axis="y", linestyle="--", alpha=0.35)


def _build_dashboard_insight_text(rows: list[dict[str, object]]) -> str:
    """Builds compact summary text for the current-run dashboard panel."""
    lines = [
        "Dashboard Notes",
        "- Bars show means with 95% CI",
        "- Compare static vs dynamic by scenario",
        "",
    ]

    grouped = _group_metric_values(rows=rows, metric_key="utility_score")
    scenarios = sorted(grouped.keys())
    for scenario in scenarios:
        static_mean = _mean(grouped[scenario].get("static", []))
        dynamic_mean = _mean(grouped[scenario].get("dynamic", []))
        diff = dynamic_mean - static_mean
        lines.append(f"{scenario}: util Δ(dynamic-static) = {diff:+.4f}")

    return "\n".join(lines)


def _build_delta_insight_text(
    previous_rows: list[dict[str, object]],
    current_rows: list[dict[str, object]],
) -> str:
    """Builds compact summary text for the delta dashboard panel."""
    lines = [
        "Delta Notes",
        "- Each panel: current mean - previous mean",
        "- Green bars: negative delta",
        "- Red bars: positive delta",
        "",
    ]

    for metric_key, _, _ in METRICS[:2]:
        previous_grouped = _group_metric_values(rows=previous_rows, metric_key=metric_key)
        current_grouped = _group_metric_values(rows=current_rows, metric_key=metric_key)
        all_deltas: list[float] = []
        for scenario in sorted(current_grouped.keys()):
            for algorithm in _ordered_algorithms(current_rows):
                prev_vals = previous_grouped.get(scenario, {}).get(algorithm, [])
                curr_vals = current_grouped.get(scenario, {}).get(algorithm, [])
                if prev_vals and curr_vals:
                    all_deltas.append(_mean(curr_vals) - _mean(prev_vals))

        lines.append(f"{metric_key}: mean delta = {_mean(all_deltas):+.4f}")

    return "\n".join(lines)


def _group_metric_values(
    rows: list[dict[str, object]],
    metric_key: str,
) -> dict[str, dict[str, list[float]]]:
    """Groups metric values by scenario and algorithm."""
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        scenario = str(row["scenario"])
        algorithm = str(row["algorithm"])
        grouped[scenario][algorithm].append(float(row[metric_key]))
    return grouped


def _ordered_algorithms(rows: list[dict[str, object]]) -> list[str]:
    """Returns algorithms with static/dynamic first if present."""
    seen = sorted({str(row["algorithm"]) for row in rows})
    preferred = [item for item in ["static", "dynamic"] if item in seen]
    rest = [item for item in seen if item not in preferred]
    return preferred + rest


def _mean(values: list[float]) -> float:
    """Returns arithmetic mean or 0 for empty input."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def _ci95(values: list[float]) -> float:
    """Returns 95% confidence interval half-width for sample mean."""
    n = len(values)
    if n <= 1:
        return 0.0

    avg = _mean(values)
    variance = sum((value - avg) ** 2 for value in values) / (n - 1)
    std_dev = math.sqrt(variance)
    return 1.96 * (std_dev / math.sqrt(n))


if __name__ == "__main__":
    main()