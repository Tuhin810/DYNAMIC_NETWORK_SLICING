from __future__ import annotations

import argparse
import threading
from time import sleep

from dashboard.server import DashboardHTTPServer
from realtime.adafruit_io import AdafruitIOClient, AdafruitIOFeedPoller, parse_adafruit_feed_spec
from realtime.state import DashboardState


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the 5G slicing dashboard and Adafruit IO poller.")
    parser.add_argument("--http-host", type=str, default="127.0.0.1")
    parser.add_argument("--http-port", type=int, default=8000)
    parser.add_argument("--policy", type=str, default="psdas", choices=["static", "dynamic", "psdas"])
    parser.add_argument("--history-limit", type=int, default=120)
    parser.add_argument("--adafruit-username", type=str, default=None)
    parser.add_argument("--adafruit-key", type=str, default=None)
    parser.add_argument(
        "--adafruit-feed",
        action="append",
        default=[],
        help="Adafruit IO feed mapping. Format: feed_key[:sensor_type[:priority[:data_rate_mbps[:sensor_id]]]]",
    )
    parser.add_argument("--adafruit-poll-interval", type=float, default=30.0)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    state = DashboardState(policy=args.policy, history_limit=args.history_limit)

    http_server = DashboardHTTPServer((args.http_host, args.http_port), state)

    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()

    if args.adafruit_username and args.adafruit_key and args.adafruit_feed:
        feeds = [parse_adafruit_feed_spec(item) for item in args.adafruit_feed]
        adafruit_client = AdafruitIOClient(username=args.adafruit_username, aio_key=args.adafruit_key)
        adafruit_poller = AdafruitIOFeedPoller(
            state=state,
            client=adafruit_client,
            feeds=feeds,
            poll_interval=args.adafruit_poll_interval,
        )
        threading.Thread(target=adafruit_poller.run_forever, daemon=True).start()
        print(f"Adafruit IO polling: {len(feeds)} feed(s) at {args.adafruit_poll_interval:.1f}s")
    elif args.adafruit_username or args.adafruit_key:
        print("Adafruit IO polling not started: provide both --adafruit-username, --adafruit-key, and at least one --adafruit-feed")

    print(f"Dashboard: http://{args.http_host}:{args.http_port}")
    if args.adafruit_feed:
        print("Adafruit IO source: enabled")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        http_server.shutdown()
        http_server.server_close()


if __name__ == "__main__":
    main()
