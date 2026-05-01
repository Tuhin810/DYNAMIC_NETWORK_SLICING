from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any, Mapping

from devices import Device


@dataclass(frozen=True)
class SensorReading:
    """Normalized sensor event accepted by the realtime socket server."""

    device_id: int
    sensor_id: str
    sensor_type: str
    data_rate_mbps: float
    priority: int
    value: float
    timestamp: float

    def to_device(self) -> Device:
        return Device(
            id=self.device_id,
            type=self.sensor_type,  # type: ignore[arg-type]
            data_rate=self.data_rate_mbps,
            priority=self.priority,
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def reading_from_payload(payload: Mapping[str, Any]) -> SensorReading:
    """Builds a sensor reading from a JSON payload."""
    try:
        device_id = int(payload["device_id"])
        sensor_id = str(payload.get("sensor_id", f"sensor-{device_id}"))
        sensor_type = str(payload["sensor_type"])
        data_rate_mbps = float(payload["data_rate_mbps"])
        priority = int(payload["priority"])
        value = float(payload["value"])
        timestamp = float(payload.get("timestamp", time.time()))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid sensor payload") from exc

    if sensor_type not in {"iot", "video", "emergency"}:
        raise ValueError(f"Unsupported sensor_type: {sensor_type}")
    if priority not in {1, 2, 3}:
        raise ValueError("priority must be 1, 2, or 3")
    if data_rate_mbps <= 0:
        raise ValueError("data_rate_mbps must be positive")

    return SensorReading(
        device_id=device_id,
        sensor_id=sensor_id,
        sensor_type=sensor_type,
        data_rate_mbps=round(data_rate_mbps, 3),
        priority=priority,
        value=round(value, 3),
        timestamp=timestamp,
    )
