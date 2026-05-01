from __future__ import annotations

import argparse
import threading
from time import sleep

from dashboard.server import DashboardHTTPServer
from realtime.demo_client import run_virtual_sensor_stream
from realtime.server import SensorTCPServer
from realtime.state import DashboardState


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the 5G slicing dashboard and socket hub.")
    parser.add_argument("--http-host", type=str, default="127.0.0.1")
    parser.add_argument("--http-port", type=int, default=8000)
    parser.add_argument("--socket-host", type=str, default="127.0.0.1")
    parser.add_argument("--socket-port", type=int, default=9100)
    parser.add_argument("--policy", type=str, default="psdas", choices=["static", "dynamic", "psdas"])
    parser.add_argument("--history-limit", type=int, default=120)
    parser.add_argument("--demo", action="store_true", help="Start a built-in virtual sensor stream.")
    parser.add_argument("--demo-device-count", type=int, default=24)
    parser.add_argument("--demo-rounds", type=int, default=40)
    parser.add_argument("--demo-interval", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    state = DashboardState(policy=args.policy, history_limit=args.history_limit)

    http_server = DashboardHTTPServer((args.http_host, args.http_port), state)
    socket_server = SensorTCPServer((args.socket_host, args.socket_port), state)

    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    socket_thread = threading.Thread(target=socket_server.serve_forever, daemon=True)
    http_thread.start()
    socket_thread.start()

    if args.demo:
        demo_thread = threading.Thread(
            target=run_virtual_sensor_stream,
            kwargs={
                "host": args.socket_host,
                "port": args.socket_port,
                "device_count": args.demo_device_count,
                "rounds": args.demo_rounds,
                "interval": args.demo_interval,
                "seed": args.seed,
            },
            daemon=True,
        )
        demo_thread.start()

    print(f"Dashboard: http://{args.http_host}:{args.http_port}")
    print(f"Socket ingest: {args.socket_host}:{args.socket_port}")
    if args.demo:
        print("Demo sensor stream: enabled")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        http_server.shutdown()
        socket_server.shutdown()
        http_server.server_close()
        socket_server.server_close()


if __name__ == "__main__":
    main()
