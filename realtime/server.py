from __future__ import annotations

import json
import socketserver
from typing import Any

from realtime.models import reading_from_payload
from realtime.state import DashboardState


class SensorTCPServer(socketserver.ThreadingTCPServer):
    """Line-delimited JSON socket server for ingesting virtual sensor data."""

    allow_reuse_address = True

    def __init__(self, server_address: tuple[str, int], state: DashboardState) -> None:
        self.state = state
        super().__init__(server_address, SensorStreamHandler)


class SensorStreamHandler(socketserver.StreamRequestHandler):
    """Receives JSON sensor events over a plain TCP socket."""

    def handle(self) -> None:
        self.wfile.write(b"connected to 5g slicing sensor hub\n")
        self.wfile.flush()

        while True:
            raw_line = self.rfile.readline()
            if not raw_line:
                break

            text = raw_line.decode("utf-8", errors="ignore").strip()
            if not text:
                continue

            try:
                payload = json.loads(text)
                reading = reading_from_payload(payload)
                snapshot = self.server.state.update_sensor(reading)  # type: ignore[attr-defined]
                response: dict[str, Any] = {
                    "ok": True,
                    "message": "ingested",
                    "total_messages": snapshot.total_messages,
                    "policy": snapshot.policy,
                    "overall_metrics": snapshot.overall_metrics,
                }
            except (json.JSONDecodeError, ValueError) as exc:
                response = {"ok": False, "error": str(exc)}

            self.wfile.write((json.dumps(response) + "\n").encode("utf-8"))
            self.wfile.flush()
