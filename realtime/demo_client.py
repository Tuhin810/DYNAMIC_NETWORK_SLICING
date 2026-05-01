from __future__ import annotations

import argparse
import json
import random
import socket
import time
from dataclasses import asdict

from devices import generate_devices


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send virtual sensor data to the socket server.")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9100)
    parser.add_argument("--device-count", type=int, default=24)
    parser.add_argument("--rounds", type=int, default=40)
    parser.add_argument("--interval", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_virtual_sensor_stream(
        host=args.host,
        port=args.port,
        device_count=args.device_count,
        rounds=args.rounds,
        interval=args.interval,
        seed=args.seed,
    )


def run_virtual_sensor_stream(
    host: str,
    port: int,
    device_count: int,
    rounds: int,
    interval: float,
    seed: int,
) -> None:
    """Continuously sends virtual sensor events to the TCP hub."""
    rng = random.Random(seed)
    devices = generate_devices(num_devices=max(100, device_count), seed=seed)[:device_count]

    with socket.create_connection((host, port), timeout=5) as connection:
        reader = connection.makefile("r", encoding="utf-8")
        writer = connection.makefile("w", encoding="utf-8")
        _ = reader.readline()

        for round_index in range(rounds):
            for device in devices:
                payload = _build_payload(device.id, device.type, device.data_rate, device.priority, rng)
                writer.write(json.dumps(payload) + "\n")
                writer.flush()
                _ = reader.readline()
                time.sleep(interval)

            print(f"sent round {round_index + 1}/{rounds}")


def _build_payload(
    device_id: int,
    sensor_type: str,
    data_rate_mbps: float,
    priority: int,
    rng: random.Random,
) -> dict[str, object]:
    observed_value = round(data_rate_mbps * (0.75 + rng.random() * 0.55), 3)
    return {
        "device_id": device_id,
        "sensor_id": f"sensor-{device_id}",
        "sensor_type": sensor_type,
        "data_rate_mbps": round(data_rate_mbps, 3),
        "priority": priority,
        "value": observed_value,
        "timestamp": time.time(),
    }


if __name__ == "__main__":
    main()
