from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from realtime.state import DashboardState


@dataclass(frozen=True)
class AdafruitFeedConfig:
    """Mapping from an Adafruit IO feed to one dashboard sensor stream."""

    feed_key: str
    sensor_type: str = "iot"
    priority: int = 2
    data_rate_mbps: float = 1.0
    sensor_id: str | None = None


class AdafruitIOClient:
    """Minimal Adafruit IO HTTP client using the documented REST API."""

    def __init__(self, username: str, aio_key: str, timeout: int = 10) -> None:
        self.username = username
        self.aio_key = aio_key
        self.timeout = timeout

    def fetch_last_data(self, feed_key: str) -> dict[str, Any]:
        """Fetches the most recent data record for a feed."""
        url = f"https://io.adafruit.com/api/v2/{self.username}/feeds/{feed_key}/data/last"
        request = Request(url, headers={"X-AIO-Key": self.aio_key})

        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as error:
            raise RuntimeError(f"Adafruit IO error {error.code} while reading feed '{feed_key}'") from error
        except URLError as error:
            raise RuntimeError(f"Unable to reach Adafruit IO for feed '{feed_key}': {error.reason}") from error

        if not payload.strip():
            raise RuntimeError(f"Adafruit IO feed '{feed_key}' returned an empty response")

        try:
            data = json.loads(payload)
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Adafruit IO feed '{feed_key}' returned invalid JSON") from error

        if not isinstance(data, dict):
            raise RuntimeError(f"Adafruit IO feed '{feed_key}' did not return a JSON object")

        return data


class AdafruitIOFeedPoller:
    """Polls configured Adafruit IO feeds and ingests them into dashboard state."""

    def __init__(
        self,
        state: DashboardState,
        client: AdafruitIOClient,
        feeds: list[AdafruitFeedConfig],
        poll_interval: float = 30.0,
    ) -> None:
        self.state = state
        self.client = client
        self.feeds = feeds
        self.poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._last_seen: dict[str, str] = {}

    def stop(self) -> None:
        self._stop_event.set()

    def run_forever(self) -> None:
        while not self._stop_event.is_set():
            self.poll_once()
            self._stop_event.wait(self.poll_interval)

    def poll_once(self) -> list[dict[str, object]]:
        """Polls each configured feed once and returns the ingested readings."""
        ingested: list[dict[str, object]] = []

        for feed in self.feeds:
            try:
                record = self.client.fetch_last_data(feed.feed_key)
                record_id = str(record.get("id") or record.get("created_at") or record.get("value"))
                if self._last_seen.get(feed.feed_key) == record_id:
                    continue

                payload = self._record_to_payload(feed=feed, record=record)
                result = self.state.ingest_payload(payload)
                self._last_seen[feed.feed_key] = record_id
                ingested.append(result)
            except Exception as error:  # noqa: BLE001
                ingested.append(
                    {
                        "ok": False,
                        "feed_key": feed.feed_key,
                        "error": str(error),
                    }
                )

        return ingested

    def _record_to_payload(self, feed: AdafruitFeedConfig, record: dict[str, Any]) -> dict[str, object]:
        sensor_value = _to_float(record.get("value", 0.0))
        created_at = record.get("created_at")
        timestamp = _created_at_to_epoch(created_at)
        sensor_id = feed.sensor_id or feed.feed_key
        device_id = _stable_device_id(feed.feed_key)

        return {
            "device_id": device_id,
            "sensor_id": sensor_id,
            "sensor_type": feed.sensor_type,
            "data_rate_mbps": feed.data_rate_mbps,
            "priority": feed.priority,
            "value": sensor_value,
            "timestamp": timestamp,
            "source": "adafruit_io",
            "feed_key": feed.feed_key,
            "created_at": created_at,
        }


def parse_adafruit_feed_spec(spec: str) -> AdafruitFeedConfig:
    """Parses a feed spec string into a polling config.

    Supported formats:
    - feed_key
    - feed_key:sensor_type:priority:data_rate_mbps
    - feed_key:sensor_type:priority:data_rate_mbps:sensor_id
    """
    parts = [part.strip() for part in spec.split(":")]
    if not parts or not parts[0]:
        raise ValueError("Feed spec must include a feed key")

    feed_key = parts[0]
    sensor_type, priority, data_rate_mbps, sensor_id = _default_feed_mapping(feed_key)

    if len(parts) > 1 and parts[1]:
        sensor_type = parts[1]
    if len(parts) > 2 and parts[2]:
        priority = int(parts[2])
    if len(parts) > 3 and parts[3]:
        data_rate_mbps = float(parts[3])
    if len(parts) > 4 and parts[4]:
        sensor_id = parts[4]

    return AdafruitFeedConfig(
        feed_key=feed_key,
        sensor_type=sensor_type,
        priority=priority,
        data_rate_mbps=data_rate_mbps,
        sensor_id=sensor_id,
    )


def _default_feed_mapping(feed_key: str) -> tuple[str, int, float, str | None]:
    lowered = feed_key.lower()
    if any(token in lowered for token in ("video", "camera", "stream")):
        return "video", 2, 12.0, feed_key
    if any(token in lowered for token in ("alarm", "emergency", "alert", "panic")):
        return "emergency", 1, 5.0, feed_key
    return "iot", 2, 1.0, feed_key


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _created_at_to_epoch(created_at: Any) -> float:
    if not created_at:
        return time.time()

    if isinstance(created_at, (int, float)):
        return float(created_at)

    if isinstance(created_at, str):
        normalized = created_at.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return time.time()
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()

    return time.time()


def _stable_device_id(feed_key: str) -> int:
    return sum((index + 1) * ord(char) for index, char in enumerate(feed_key)) % 10_000_000
