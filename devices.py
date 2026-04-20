from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Literal

DeviceType = Literal["iot", "video", "emergency"]


@dataclass(frozen=True)
class Device:
    """Represents a virtual device in the 5G slicing simulation."""

    id: int
    type: DeviceType
    data_rate: float
    priority: int


def _sample_device_type(rng: Random) -> DeviceType:
    """Returns a device type using a realistic traffic mix."""
    roll = rng.random()
    if roll < 0.60:
        return "iot"
    if roll < 0.90:
        return "video"
    return "emergency"


def _sample_profile(device_type: DeviceType, rng: Random) -> tuple[float, int]:
    """Creates data rate (Mbps) and priority (1 high -> 3 low)."""
    if device_type == "iot":
        data_rate = rng.uniform(0.05, 1.00)
        priority = 2 if rng.random() < 0.35 else 3
    elif device_type == "video":
        data_rate = rng.uniform(8.0, 40.0)
        if rng.random() < 0.10:
            priority = 1
        elif rng.random() < 0.75:
            priority = 2
        else:
            priority = 3
    else:
        data_rate = rng.uniform(1.0, 10.0)
        priority = 1 if rng.random() < 0.80 else 2

    return round(data_rate, 2), priority


def generate_devices(num_devices: int = 120, seed: int | None = 42) -> list[Device]:
    """Generates virtual devices for simulation.

    At least 100 devices are required to keep simulation scale meaningful.
    """
    if num_devices < 100:
        raise ValueError("num_devices must be at least 100")

    rng = Random(seed)
    devices: list[Device] = []

    for device_id in range(1, num_devices + 1):
        device_type = _sample_device_type(rng)
        data_rate, priority = _sample_profile(device_type, rng)
        devices.append(
            Device(
                id=device_id,
                type=device_type,
                data_rate=data_rate,
                priority=priority,
            )
        )

    return devices
