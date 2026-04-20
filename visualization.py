from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from simulation import SimulationResult


def generate_comparison_graphs(
    static_result: SimulationResult,
    dynamic_result: SimulationResult,
    output_dir: str = "outputs",
) -> list[str]:
    """Creates latency and throughput comparison plots and returns file paths."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    slices = ["mMTC", "eMBB", "URLLC"]

    latency_static = [static_result.slice_summary[s].avg_latency_ms for s in slices]
    latency_dynamic = [dynamic_result.slice_summary[s].avg_latency_ms for s in slices]

    throughput_static = [static_result.slice_summary[s].avg_throughput_mbps for s in slices]
    throughput_dynamic = [dynamic_result.slice_summary[s].avg_throughput_mbps for s in slices]

    latency_file = output_path / "latency_comparison.png"
    throughput_file = output_path / "throughput_comparison.png"

    _plot_grouped_bars(
        slices=slices,
        static_values=latency_static,
        dynamic_values=latency_dynamic,
        y_label="Average Latency (ms)",
        title="Latency Comparison: Static vs Dynamic Slicing",
        output_file=latency_file,
    )

    _plot_grouped_bars(
        slices=slices,
        static_values=throughput_static,
        dynamic_values=throughput_dynamic,
        y_label="Average Throughput (Mbps)",
        title="Throughput Comparison: Static vs Dynamic Slicing",
        output_file=throughput_file,
    )

    return [str(latency_file), str(throughput_file)]


def _plot_grouped_bars(
    slices: list[str],
    static_values: list[float],
    dynamic_values: list[float],
    y_label: str,
    title: str,
    output_file: Path,
) -> None:
    """Helper to draw side-by-side bars for each slice."""
    width = 0.35
    x_positions = list(range(len(slices)))

    static_pos = [x - width / 2 for x in x_positions]
    dynamic_pos = [x + width / 2 for x in x_positions]

    fig, ax = plt.subplots(figsize=(9, 5))

    bars_static = ax.bar(
        static_pos,
        static_values,
        width=width,
        label="Static",
        color="#4C78A8",
    )
    bars_dynamic = ax.bar(
        dynamic_pos,
        dynamic_values,
        width=width,
        label="Dynamic",
        color="#F58518",
    )

    ax.set_title(title)
    ax.set_ylabel(y_label)
    ax.set_xlabel("Network Slice")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(slices)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    for bar in list(bars_static) + list(bars_dynamic):
        height = bar.get_height()
        ax.annotate(
            f"{height:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    fig.tight_layout()
    fig.savefig(output_file, dpi=150)
    plt.close(fig)
