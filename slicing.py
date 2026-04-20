from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Iterable, Mapping

from devices import Device


@dataclass(frozen=True)
class SliceProfile:
    """Defines slice-level constraints and behavior."""

    name: str
    bandwidth_capacity_mbps: float
    base_latency_ms: float
    device_capacity: int


SLICES: dict[str, SliceProfile] = {
    "mMTC": SliceProfile(
        name="mMTC",
        bandwidth_capacity_mbps=250.0,
        base_latency_ms=50.0,
        device_capacity=1200,
    ),
    "eMBB": SliceProfile(
        name="eMBB",
        bandwidth_capacity_mbps=800.0,
        base_latency_ms=20.0,
        device_capacity=300,
    ),
    "URLLC": SliceProfile(
        name="URLLC",
        bandwidth_capacity_mbps=350.0,
        base_latency_ms=5.0,
        device_capacity=150,
    ),
}

PREFERRED_SLICE: dict[str, str] = {
    "iot": "mMTC",
    "video": "eMBB",
    "emergency": "URLLC",
}

MISMATCH_COST: dict[str, dict[str, float]] = {
    "iot": {"mMTC": 0.0, "eMBB": 20.0, "URLLC": 35.0},
    "video": {"mMTC": 40.0, "eMBB": 0.0, "URLLC": 25.0},
    "emergency": {"mMTC": 90.0, "eMBB": 50.0, "URLLC": 0.0},
}


def default_background_load(seed: int | None = None) -> dict[str, float]:
    """Returns background load ratios (0.0-1.0) to emulate external traffic."""
    rng = Random(seed)
    return {
        "mMTC": round(rng.uniform(0.20, 0.50), 2),
        "eMBB": round(rng.uniform(0.25, 0.55), 2),
        "URLLC": round(rng.uniform(0.10, 0.35), 2),
    }


def assign_static_slices(devices: Iterable[Device]) -> dict[int, str]:
    """Type-based static assignment used as baseline."""
    return {device.id: PREFERRED_SLICE[device.type] for device in devices}


def assign_dynamic_slices(
    devices: Iterable[Device],
    background_load: Mapping[str, float] | None = None,
) -> dict[int, str]:
    """Load-aware assignment that also respects device priority.

    High-priority devices are allocated first and are more strongly biased
    towards low-latency and non-overloaded slices.
    """
    if background_load is None:
        background_load = {"mMTC": 0.30, "eMBB": 0.30, "URLLC": 0.20}

    current_rate = {slice_name: 0.0 for slice_name in SLICES}
    current_count = {slice_name: 0 for slice_name in SLICES}
    assignments: dict[int, str] = {}

    ordered_devices = sorted(devices, key=lambda item: (item.priority, -item.data_rate))

    for device in ordered_devices:
        current_load = {
            slice_name: background_load[slice_name]
            + (current_rate[slice_name] / SLICES[slice_name].bandwidth_capacity_mbps)
            for slice_name in SLICES
        }
        network_load = sum(current_load.values()) / len(SLICES)
        preferred_slice = dynamic_slice(
            device=device,
            network_load=network_load,
            slice_load=current_load,
        )

        best_slice = min(
            SLICES,
            key=lambda slice_name: _slice_score(
                device=device,
                slice_name=slice_name,
                current_rate=current_rate,
                current_count=current_count,
                background_load=background_load,
                preferred_slice=preferred_slice,
            ),
        )

        assignments[device.id] = best_slice
        current_rate[best_slice] += device.data_rate
        current_count[best_slice] += 1

    return assignments


def dynamic_slice(
    device: Device,
    network_load: float,
    slice_load: Mapping[str, float],
) -> str:
    """Rule-based dynamic pre-selection using load and priority.

    This function acts as a fast online policy. Final selection is still
    score-based, but this preferred slice nudges decisions under congestion.
    """
    # High-priority or emergency traffic should prefer URLLC.
    if device.priority == 1 or device.type == "emergency":
        return "URLLC"

    # During global congestion, move best-effort traffic to high-capacity slices.
    if network_load > 0.70:
        if device.type == "iot":
            return "mMTC"

        if device.type == "video" and device.priority >= 2:
            return "mMTC" if slice_load["mMTC"] <= slice_load["eMBB"] else "eMBB"

    if device.type == "video":
        return "eMBB"

    return "mMTC"


def _slice_score(
    device: Device,
    slice_name: str,
    current_rate: Mapping[str, float],
    current_count: Mapping[str, int],
    background_load: Mapping[str, float],
    preferred_slice: str | None = None,
) -> float:
    """Computes an allocation score for assigning a device to a slice."""
    profile = SLICES[slice_name]

    if current_count[slice_name] + 1 > profile.device_capacity:
        return float("inf")

    projected_load = background_load[slice_name] + (
        (current_rate[slice_name] + device.data_rate) / profile.bandwidth_capacity_mbps
    )

    overload_penalty = max(0.0, projected_load - 1.0) * 250.0
    latency_penalty = profile.base_latency_ms * (1.0 + projected_load)
    mismatch_penalty = MISMATCH_COST[device.type][slice_name]
    balance_penalty = projected_load * 12.0

    priority_weight = {1: 1.45, 2: 1.00, 3: 0.70}[device.priority]

    # Protect emergency traffic under load by strongly favoring URLLC.
    if device.priority == 1 and slice_name != "URLLC":
        mismatch_penalty += 20.0

    policy_bonus = 0.0
    if preferred_slice == slice_name:
        policy_bonus = {1: 18.0, 2: 12.0, 3: 8.0}[device.priority]

    return (
        (latency_penalty + overload_penalty) * priority_weight
        + mismatch_penalty
        + balance_penalty
        - policy_bonus
    )


def count_devices_per_slice(assignments: Mapping[int, str]) -> dict[str, int]:
    """Builds a simple count summary from assignment output."""
    counts = {slice_name: 0 for slice_name in SLICES}
    for slice_name in assignments.values():
        counts[slice_name] += 1
    return counts
