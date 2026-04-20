from __future__ import annotations

from dataclasses import asdict, dataclass
from random import Random
from typing import Literal

from devices import Device

DeviceType = Literal["iot", "video", "emergency"]


@dataclass(frozen=True)
class ScenarioPreset:
    """Defines a fixed experiment scenario with traffic and load parameters."""

    name: str
    description: str
    num_devices: int
    device_mix: dict[DeviceType, float]
    background_load: dict[str, float]


@dataclass(frozen=True)
class ExperimentRunConfig:
    """Records the exact configuration used for one experiment run."""

    scenario_name: str
    algorithm: str
    num_devices: int
    seed: int
    device_mix: dict[DeviceType, float]
    background_load: dict[str, float]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


SCENARIO_PRESETS: dict[str, ScenarioPreset] = {
    "balanced": ScenarioPreset(
        name="balanced",
        description="Balanced traffic mix close to nominal network conditions.",
        num_devices=180,
        device_mix={"iot": 0.60, "video": 0.30, "emergency": 0.10},
        background_load={"mMTC": 0.30, "eMBB": 0.36, "URLLC": 0.20},
    ),
    "video_heavy": ScenarioPreset(
        name="video_heavy",
        description="Video-heavy traffic stressing eMBB capacity.",
        num_devices=180,
        device_mix={"iot": 0.35, "video": 0.55, "emergency": 0.10},
        background_load={"mMTC": 0.30, "eMBB": 0.52, "URLLC": 0.22},
    ),
    "emergency_burst": ScenarioPreset(
        name="emergency_burst",
        description="Higher emergency share and elevated URLLC pressure.",
        num_devices=180,
        device_mix={"iot": 0.50, "video": 0.28, "emergency": 0.22},
        background_load={"mMTC": 0.32, "eMBB": 0.38, "URLLC": 0.34},
    ),
    "high_congestion": ScenarioPreset(
        name="high_congestion",
        description="System-wide high background load on all slices.",
        num_devices=220,
        device_mix={"iot": 0.55, "video": 0.33, "emergency": 0.12},
        background_load={"mMTC": 0.55, "eMBB": 0.60, "URLLC": 0.46},
    ),
    "noisy_channel": ScenarioPreset(
        name="noisy_channel",
        description="Noisy channel proxy with slightly elevated baseline loads.",
        num_devices=200,
        device_mix={"iot": 0.58, "video": 0.30, "emergency": 0.12},
        background_load={"mMTC": 0.42, "eMBB": 0.48, "URLLC": 0.30},
    ),
}


def list_scenario_names() -> list[str]:
    """Returns all supported scenario names in deterministic order."""
    return list(SCENARIO_PRESETS.keys())


def get_scenario_preset(name: str) -> ScenarioPreset:
    """Returns scenario preset by name with validation."""
    if name not in SCENARIO_PRESETS:
        available = ", ".join(list_scenario_names())
        raise ValueError(f"Unknown scenario '{name}'. Available scenarios: {available}")
    return SCENARIO_PRESETS[name]


def generate_devices_for_scenario(
    scenario: ScenarioPreset,
    seed: int,
    num_devices: int | None = None,
) -> list[Device]:
    """Generates deterministic scenario-specific devices for experiment runs."""
    total_devices = scenario.num_devices if num_devices is None else num_devices
    if total_devices < 100:
        raise ValueError("num_devices must be at least 100")

    rng = Random(seed)
    devices: list[Device] = []

    for device_id in range(1, total_devices + 1):
        device_type = _sample_device_type_from_mix(rng, scenario.device_mix)
        data_rate, priority = _sample_profile(device_type=device_type, rng=rng)
        devices.append(
            Device(
                id=device_id,
                type=device_type,
                data_rate=data_rate,
                priority=priority,
            )
        )

    return devices


def _sample_device_type_from_mix(
    rng: Random,
    mix: dict[DeviceType, float],
) -> DeviceType:
    """Samples a device type according to a validated probability mix."""
    roll = rng.random()

    iot_cutoff = mix["iot"]
    video_cutoff = mix["iot"] + mix["video"]

    if roll < iot_cutoff:
        return "iot"
    if roll < video_cutoff:
        return "video"
    return "emergency"


def _sample_profile(device_type: DeviceType, rng: Random) -> tuple[float, int]:
    """Samples data rate and priority with type-specific behavior."""
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