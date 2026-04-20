from __future__ import annotations

import argparse

from devices import generate_devices
from simulation import SimulationResult, simulate_network_performance
from slicing import (
    SLICES,
    assign_dynamic_slices,
    assign_static_slices,
    default_background_load,
)
from visualization import generate_comparison_graphs


def interactive_menu() -> str:
    """Simple CLI menu for selecting slicing mode."""
    print("\n5G Network Slicing Simulation Menu")
    print("1. Static slicing")
    print("2. Dynamic slicing")
    print("3. Compare static vs dynamic")

    choice = input("Select option [1-3]: ").strip()
    if choice == "1":
        return "static"
    if choice == "2":
        return "dynamic"
    return "compare"


def print_summary(result: SimulationResult) -> None:
    """Prints required summary KPIs for each slice."""
    print(f"\n=== {result.mode.upper()} SLICING SUMMARY ===")
    print(
        f"{'Slice':<8}{'Devices':>10}{'Avg Latency (ms)':>20}"
        f"{'P95 Latency':>14}{'P99 Latency':>14}{'Avg Throughput (Mbps)':>24}"
        f"{'Avg Packet Loss (%)':>22}{'SLA Viol. (%)':>14}{'Load Ratio':>14}"
    )

    for slice_name in SLICES:
        item = result.slice_summary[slice_name]
        print(
            f"{slice_name:<8}{item.device_count:>10}{item.avg_latency_ms:>20.3f}"
            f"{item.p95_latency_ms:>14.3f}{item.p99_latency_ms:>14.3f}"
            f"{item.avg_throughput_mbps:>24.3f}{item.avg_packet_loss_pct:>22.3f}"
            f"{item.sla_violation_rate_pct:>14.3f}"
            f"{item.load_ratio:>14.3f}"
        )

    print(
        "\nOverall metrics: "
        f"SLA Violations={result.overall_sla_violation_count} "
        f"({result.overall_sla_violation_rate_pct:.3f}%), "
        f"Fairness={result.fairness_index:.4f}, "
        f"Utility={result.utility_score:.4f}"
    )


def print_comparison(static_result: SimulationResult, dynamic_result: SimulationResult) -> None:
    """Prints static vs dynamic difference for easy interpretation."""
    print("\n=== DYNAMIC VS STATIC DIFFERENCE ===")
    print(
        f"{'Slice':<8}{'Latency Change (%)':>20}{'Throughput Change (%)':>24}"
        f"{'Packet Loss Change (%)':>24}"
    )

    for slice_name in SLICES:
        static_item = static_result.slice_summary[slice_name]
        dynamic_item = dynamic_result.slice_summary[slice_name]

        latency_change = _percent_change(
            old=static_item.avg_latency_ms,
            new=dynamic_item.avg_latency_ms,
        )
        throughput_change = _percent_change(
            old=static_item.avg_throughput_mbps,
            new=dynamic_item.avg_throughput_mbps,
        )
        packet_loss_change = _percent_change(
            old=static_item.avg_packet_loss_pct,
            new=dynamic_item.avg_packet_loss_pct,
        )

        print(
            f"{slice_name:<8}{latency_change:>20.2f}{throughput_change:>24.2f}"
            f"{packet_loss_change:>24.2f}"
        )

    print("\nNote: lower values are better for latency and packet loss.")


def _percent_change(old: float, new: float) -> float:
    """Returns percentage change from old to new."""
    if old == 0:
        return 0.0
    return ((new - old) / old) * 100.0


def run_mode(mode: str, num_devices: int, seed: int, output_dir: str) -> None:
    """Executes selected mode end-to-end."""
    if num_devices < 100:
        print("Requested devices < 100, using 100 to satisfy simulation requirement.")
        num_devices = 100

    devices = generate_devices(num_devices=num_devices, seed=seed)
    background_load = default_background_load(seed + 100)

    if mode == "static":
        static_assignments = assign_static_slices(devices)
        static_result = simulate_network_performance(
            devices=devices,
            assignments=static_assignments,
            mode="static",
            seed=seed + 1,
            background_load=background_load,
        )
        print_summary(static_result)
        return

    if mode == "dynamic":
        dynamic_assignments = assign_dynamic_slices(
            devices=devices,
            background_load=background_load,
        )
        dynamic_result = simulate_network_performance(
            devices=devices,
            assignments=dynamic_assignments,
            mode="dynamic",
            seed=seed + 2,
            background_load=background_load,
        )
        print_summary(dynamic_result)
        return

    static_assignments = assign_static_slices(devices)
    dynamic_assignments = assign_dynamic_slices(
        devices=devices,
        background_load=background_load,
    )

    static_result = simulate_network_performance(
        devices=devices,
        assignments=static_assignments,
        mode="static",
        seed=seed + 1,
        background_load=background_load,
    )
    dynamic_result = simulate_network_performance(
        devices=devices,
        assignments=dynamic_assignments,
        mode="dynamic",
        seed=seed + 2,
        background_load=background_load,
    )

    print_summary(static_result)
    print_summary(dynamic_result)
    print_comparison(static_result, dynamic_result)

    graph_paths = generate_comparison_graphs(
        static_result=static_result,
        dynamic_result=dynamic_result,
        output_dir=output_dir,
    )

    print("\nGenerated comparison graphs:")
    for path in graph_paths:
        print(f"- {path}")


def parse_args() -> argparse.Namespace:
    """Parses command line options for simulation."""
    parser = argparse.ArgumentParser(
        description="5G network slicing simulation for IoT/video/emergency devices."
    )
    parser.add_argument(
        "--mode",
        choices=["menu", "static", "dynamic", "compare"],
        default="menu",
        help="Simulation mode. 'menu' shows an interactive selector.",
    )
    parser.add_argument(
        "--devices",
        type=int,
        default=120,
        help="Number of virtual devices to generate (minimum 100).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible experiments.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Directory to save generated graphs.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    selected_mode = args.mode
    if selected_mode == "menu":
        selected_mode = interactive_menu()

    run_mode(
        mode=selected_mode,
        num_devices=args.devices,
        seed=args.seed,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
