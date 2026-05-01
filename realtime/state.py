from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from typing import Deque

from devices import Device
from simulation import SimulationResult, SliceSummary, simulate_network_performance
from slicing import (
    SLICES,
    assign_dynamic_slices,
    assign_psdas_slices,
    assign_static_slices,
    default_background_load,
)

from realtime.models import SensorReading
from realtime.models import reading_from_payload


@dataclass(frozen=True)
class LiveSnapshot:
    """Serializable state shown by the dashboard."""

    policy: str
    total_messages: int
    active_devices: int
    updated_at: float
    status: str
    background_load: dict[str, float]
    overall_metrics: dict[str, float]
    slice_summary: dict[str, dict[str, object]]
    recent_readings: list[dict[str, object]]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class DashboardState:
    """Thread-safe store for ingested sensor readings and live metrics."""

    def __init__(
        self,
        policy: str = "psdas",
        background_load: dict[str, float] | None = None,
        history_limit: int = 120,
    ) -> None:
        self._policy = policy
        self._background_load = dict(background_load or default_background_load(42))
        self._readings: Deque[SensorReading] = deque(maxlen=history_limit)
        self._lock = threading.Lock()
        self._latest_snapshot = self._build_empty_snapshot()

    @property
    def policy(self) -> str:
        return self._policy

    def update_sensor(self, reading: SensorReading) -> LiveSnapshot:
        """Adds one sensor event and refreshes the dashboard snapshot."""
        with self._lock:
            self._readings.append(reading)
            self._latest_snapshot = self._recompute_snapshot()
            return self._latest_snapshot

    def snapshot(self) -> dict[str, object]:
        """Returns the current state as JSON-ready data."""
        with self._lock:
            return self._latest_snapshot.to_dict()

    def ingest_payload(self, payload: dict[str, object]) -> dict[str, object]:
        """Validates one REST payload and refreshes the live snapshot."""
        reading = reading_from_payload(payload)
        snapshot = self.update_sensor(reading)
        return {
            "ok": True,
            "message": "ingested",
            "reading": reading.to_dict(),
            "snapshot": snapshot.to_dict(),
        }

    def _build_empty_snapshot(self) -> LiveSnapshot:
        slice_summary = {
            slice_name: {
                "device_count": 0,
                "avg_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
                "avg_throughput_mbps": 0.0,
                "avg_packet_loss_pct": 0.0,
                "sla_violation_count": 0,
                "sla_violation_rate_pct": 0.0,
                "load_ratio": round(self._background_load.get(slice_name, 0.0), 3),
            }
            for slice_name in SLICES
        }

        return LiveSnapshot(
            policy=self._policy,
            total_messages=0,
            active_devices=0,
            updated_at=time.time(),
            status="waiting for sensor data",
            background_load=dict(self._background_load),
            overall_metrics={
                "overall_sla_violation_count": 0,
                "overall_sla_violation_rate_pct": 0.0,
                "fairness_index": 0.0,
                "utility_score": 0.0,
            },
            slice_summary=slice_summary,
            recent_readings=[],
        )

    def _recompute_snapshot(self) -> LiveSnapshot:
        readings = list(self._readings)
        if not readings:
            return self._build_empty_snapshot()

        devices = [reading.to_device() for reading in readings]
        assignments = self._assign_devices(devices)
        result = simulate_network_performance(
            devices=devices,
            assignments=assignments,
            mode=self._policy,
            seed=1000 + len(readings),
            background_load=self._background_load,
        )

        slice_summary = self._serialize_slice_summary(result, assignments)
        recent_readings = self._build_recent_readings(readings, assignments)

        return LiveSnapshot(
            policy=self._policy,
            total_messages=len(readings),
            active_devices=len(devices),
            updated_at=time.time(),
            status="live sensor stream active",
            background_load=dict(self._background_load),
            overall_metrics={
                "overall_sla_violation_count": result.overall_sla_violation_count,
                "overall_sla_violation_rate_pct": result.overall_sla_violation_rate_pct,
                "fairness_index": result.fairness_index,
                "utility_score": result.utility_score,
            },
            slice_summary=slice_summary,
            recent_readings=recent_readings,
        )

    def _assign_devices(self, devices: list[Device]) -> dict[int, str]:
        if self._policy == "static":
            return assign_static_slices(devices)
        if self._policy == "dynamic":
            return assign_dynamic_slices(devices=devices, background_load=self._background_load)
        return assign_psdas_slices(devices=devices, background_load=self._background_load)

    def _serialize_slice_summary(
        self,
        result: SimulationResult,
        assignments: dict[int, str],
    ) -> dict[str, dict[str, object]]:
        assigned_counts = {slice_name: 0 for slice_name in SLICES}
        for slice_name in assignments.values():
            assigned_counts[slice_name] += 1

        serialized: dict[str, dict[str, object]] = {}
        for slice_name, summary in result.slice_summary.items():
            serialized[slice_name] = {
                **asdict(summary),
                "assigned_devices": assigned_counts[slice_name],
            }
        return serialized

    def _build_recent_readings(
        self,
        readings: list[SensorReading],
        assignments: dict[int, str],
        limit: int = 12,
    ) -> list[dict[str, object]]:
        recent = readings[-limit:]
        return [
            {
                **reading.to_dict(),
                "assigned_slice": assignments.get(reading.device_id, "unknown"),
            }
            for reading in reversed(recent)
        ]
