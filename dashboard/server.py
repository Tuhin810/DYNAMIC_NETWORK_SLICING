from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from realtime.state import DashboardState


STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


class DashboardHTTPServer(ThreadingHTTPServer):
    """HTTP server that exposes the dashboard page and JSON state endpoint."""

    def __init__(self, server_address: tuple[str, int], state: DashboardState) -> None:
        self.state = state
        super().__init__(server_address, DashboardRequestHandler)


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """Serves the dashboard UI and live state JSON."""

    server: DashboardHTTPServer

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/index.html"}:
            self._serve_index()
            return

        if self.path == "/api/state":
            self._serve_json(self.server.state.snapshot())
            return

        if self.path == "/api/health":
            self._serve_json({"ok": True, "service": "dashboard"})
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _serve_index(self) -> None:
        html = STATIC_INDEX.read_text(encoding="utf-8")
        body = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_json(self, payload: dict[str, object], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

