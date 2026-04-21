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

SLA_TARGETS: dict[str, dict[str, float | None]] = {
    "mMTC": {"max_latency_ms": 80.0, "min_throughput_mbps": None, "max_packet_loss_pct": 3.0},
    "eMBB": {"max_latency_ms": None, "min_throughput_mbps": 25.0, "max_packet_loss_pct": 2.0},
    "URLLC": {"max_latency_ms": 10.0, "min_throughput_mbps": None, "max_packet_loss_pct": 1.0},
}


@dataclass(frozen=True)
class PsdasConfig:
    """Control knobs for PSDAS and ablation toggles."""

    prediction_alpha: float = 0.35
    debt_gain: float = 1.10
    overload_guard: float = 0.92
    no_prediction: bool = False
    no_debt: bool = False
    fixed_weights: bool = False


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


def assign_psdas_slices(
    devices: Iterable[Device],
    background_load: Mapping[str, float] | None = None,
    prediction_alpha: float = 0.35,
    debt_gain: float = 1.10,
    overload_guard: float = 0.92,
    no_prediction: bool = False,
    no_debt: bool = False,
    fixed_weights: bool = False,
) -> dict[int, str]:
    """Predictive SLA-Debt Aware Slicing (PSDAS) assignment policy."""
    config = _validate_psdas_config(
        PsdasConfig(
            prediction_alpha=prediction_alpha,
            debt_gain=debt_gain,
            overload_guard=overload_guard,
            no_prediction=no_prediction,
            no_debt=no_debt,
            fixed_weights=fixed_weights,
        )
    )

    if background_load is None:
        background_load = {"mMTC": 0.30, "eMBB": 0.30, "URLLC": 0.20}

    current_rate = {slice_name: 0.0 for slice_name in SLICES}
    current_count = {slice_name: 0 for slice_name in SLICES}
    predicted_load = {slice_name: float(background_load[slice_name]) for slice_name in SLICES}
    debt = {
        traffic_class: {slice_name: 0.0 for slice_name in SLICES}
        for traffic_class in ("iot", "video", "emergency")
    }

    assignments: dict[int, str] = {}
    ordered_devices = sorted(devices, key=lambda item: (item.priority, -item.data_rate))

    for device in ordered_devices:
        current_load = {
            slice_name: background_load[slice_name]
            + (current_rate[slice_name] / SLICES[slice_name].bandwidth_capacity_mbps)
            for slice_name in SLICES
        }

        if config.no_prediction:
            predicted_load = dict(current_load)
        else:
            predicted_load = {
                slice_name: (
                    (config.prediction_alpha * current_load[slice_name])
                    + ((1.0 - config.prediction_alpha) * predicted_load[slice_name])
                )
                for slice_name in SLICES
            }

        best_slice = min(
            SLICES,
            key=lambda slice_name: _psdas_slice_score(
                device=device,
                slice_name=slice_name,
                current_rate=current_rate,
                current_count=current_count,
                current_load=current_load,
                predicted_load=predicted_load,
                debt=debt,
                config=config,
            ),
        )

        assignments[device.id] = best_slice
        current_rate[best_slice] += device.data_rate
        current_count[best_slice] += 1

        if not config.no_debt:
            _update_psdas_debt(
                device=device,
                selected_slice=best_slice,
                debt=debt,
                current_rate=current_rate,
                background_load=background_load,
                config=config,
            )

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


def _validate_psdas_config(config: PsdasConfig) -> PsdasConfig:
    """Validates PSDAS tuning parameters for stable behavior."""
    if not 0.0 < config.prediction_alpha <= 1.0:
        raise ValueError("prediction_alpha must be in (0.0, 1.0]")
    if not 0.0 <= config.debt_gain <= 5.0:
        raise ValueError("debt_gain must be in [0.0, 5.0]")
    if not 0.5 <= config.overload_guard <= 1.5:
        raise ValueError("overload_guard must be in [0.5, 1.5]")
    return config


def _psdas_slice_score(
    device: Device,
    slice_name: str,
    current_rate: Mapping[str, float],
    current_count: Mapping[str, int],
    current_load: Mapping[str, float],
    predicted_load: Mapping[str, float],
    debt: Mapping[str, Mapping[str, float]],
    config: PsdasConfig,
) -> float:
    """Computes PSDAS score combining predictive load, debt, and adaptive objectives."""
    profile = SLICES[slice_name]
    if current_count[slice_name] + 1 > profile.device_capacity:
        return float("inf")

    projected_now = current_load[slice_name] + (device.data_rate / profile.bandwidth_capacity_mbps)
    projected_predicted = projected_now if config.no_prediction else max(
        projected_now,
        (0.65 * predicted_load[slice_name]) + (0.35 * projected_now),
    )

    estimated_latency, estimated_throughput, estimated_loss = _estimate_projected_metrics(
        device=device,
        slice_name=slice_name,
        projected_load=projected_predicted,
    )

    threshold = SLA_TARGETS[slice_name]
    latency_target = threshold["max_latency_ms"] or 60.0
    throughput_target = threshold["min_throughput_mbps"]
    loss_target = threshold["max_packet_loss_pct"] or 3.0

    latency_penalty = estimated_latency / max(1.0, latency_target)
    if throughput_target is None:
        throughput_penalty = max(0.0, 1.0 - (estimated_throughput / max(0.1, device.data_rate)))
    else:
        throughput_penalty = max(0.0, (throughput_target - estimated_throughput) / throughput_target)
    loss_penalty = estimated_loss / max(0.1, loss_target)

    mismatch_penalty = MISMATCH_COST[device.type][slice_name] / 40.0
    guard_penalty = max(0.0, projected_predicted - config.overload_guard) * 4.0
    overload_penalty = max(0.0, projected_now - 1.0) * 6.0

    weight_latency, weight_throughput, weight_loss = _psdas_objective_weights(
        device=device,
        debt=debt,
        fixed_weights=config.fixed_weights,
    )

    debt_penalty = 0.0 if config.no_debt else debt[device.type][slice_name] * config.debt_gain
    preference_bonus = 0.25 if slice_name == PREFERRED_SLICE[device.type] else 0.0

    return (
        (weight_latency * latency_penalty)
        + (weight_throughput * throughput_penalty)
        + (weight_loss * loss_penalty)
        + mismatch_penalty
        + guard_penalty
        + overload_penalty
        + debt_penalty
        - preference_bonus
    )


def _psdas_objective_weights(
    device: Device,
    debt: Mapping[str, Mapping[str, float]],
    fixed_weights: bool,
) -> tuple[float, float, float]:
    """Returns adaptive latency/throughput/loss weights for PSDAS scoring."""
    if fixed_weights:
        return 0.40, 0.35, 0.25

    base = {
        1: [0.58, 0.24, 0.18],
        2: [0.42, 0.36, 0.22],
        3: [0.30, 0.48, 0.22],
    }[device.priority]
    debt_pressure = sum(debt[device.type].values()) / len(SLICES)

    base[0] += min(0.25, 0.12 * debt_pressure)
    base[2] += min(0.18, 0.08 * debt_pressure)
    base[1] = max(0.10, base[1] - min(0.25, 0.15 * debt_pressure))

    total = base[0] + base[1] + base[2]
    return base[0] / total, base[1] / total, base[2] / total


def _estimate_projected_metrics(
    device: Device,
    slice_name: str,
    projected_load: float,
) -> tuple[float, float, float]:
    """Approximates SLA-facing metrics for online scoring and debt updates."""
    profile = SLICES[slice_name]
    congestion = max(0.0, projected_load - 1.0)

    priority_latency = {1: 0.80, 2: 1.00, 3: 1.15}[device.priority]
    priority_loss = {1: 0.65, 2: 1.00, 3: 1.25}[device.priority]

    estimated_latency = profile.base_latency_ms * priority_latency * (
        1.0 + (0.9 * projected_load) + (2.5 * congestion)
    )

    efficiency = 1.0 - (0.22 * max(0.0, projected_load - 0.70)) - (0.35 * congestion)
    efficiency += 0.06 * ((4 - device.priority) / 3)
    efficiency = max(0.25, min(1.00, efficiency))
    estimated_throughput = device.data_rate * efficiency

    base_loss = {"mMTC": 1.2, "eMBB": 0.8, "URLLC": 0.15}[slice_name]
    estimated_loss = base_loss * priority_loss * (
        1.0 + (3.5 * congestion) + max(0.0, projected_load - 0.80)
    )
    estimated_loss *= 0.82

    return estimated_latency, estimated_throughput, estimated_loss


def _estimate_sla_risk(
    device: Device,
    slice_name: str,
    projected_load: float,
) -> float:
    """Returns normalized SLA risk in [0, 1] for debt updates."""
    latency, throughput, loss = _estimate_projected_metrics(
        device=device,
        slice_name=slice_name,
        projected_load=projected_load,
    )

    threshold = SLA_TARGETS[slice_name]
    checks: list[bool] = []
    if threshold["max_latency_ms"] is not None:
        checks.append(latency > float(threshold["max_latency_ms"]))
    if threshold["min_throughput_mbps"] is not None:
        checks.append(throughput < float(threshold["min_throughput_mbps"]))
    if threshold["max_packet_loss_pct"] is not None:
        checks.append(loss > float(threshold["max_packet_loss_pct"]))

    if not checks:
        return 0.0

    return sum(1.0 for item in checks if item) / len(checks)


def _update_psdas_debt(
    device: Device,
    selected_slice: str,
    debt: dict[str, dict[str, float]],
    current_rate: Mapping[str, float],
    background_load: Mapping[str, float],
    config: PsdasConfig,
) -> None:
    """Updates class-slice SLA debt after each online assignment decision."""
    traffic_class = device.type

    for slice_name in SLICES:
        debt[traffic_class][slice_name] *= 0.94

    profile = SLICES[selected_slice]
    projected_load = background_load[selected_slice] + (
        current_rate[selected_slice] / profile.bandwidth_capacity_mbps
    )
    risk = _estimate_sla_risk(
        device=device,
        slice_name=selected_slice,
        projected_load=projected_load,
    )

    recovery = 0.08 * (1.0 - risk)
    debt_value = debt[traffic_class][selected_slice] + (config.debt_gain * risk) - recovery
    debt[traffic_class][selected_slice] = max(0.0, min(4.0, debt_value))


def count_devices_per_slice(assignments: Mapping[int, str]) -> dict[str, int]:
    """Builds a simple count summary from assignment output."""
    counts = {slice_name: 0 for slice_name in SLICES}
    for slice_name in assignments.values():
        counts[slice_name] += 1
    return counts
