"""A simulated scanner device. It registers, sends heartbeats and writes scan data and a log.

Day 2 starter: the files go to a local folder (outbox/). On Day 5 the same files are uploaded to
the landing bucket under the same names. Standard library only, so it runs anywhere Python does.

    python simulator/scanner_sim.py --device-id scanner-007 --city pune --scans 3
"""

import argparse
import json
import random
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path


def object_key(city: str, device_id: str, when: datetime, kind: str, number: int = 0) -> str:
    """Name of one upload: <city>/<device-id>/<date>/<kind>-<time>[-<number>].<ext>.

    kind is scan or log. The scan number keeps two scans of the same second apart.
    """
    extension = {"scan": "json", "log": "log"}[kind]
    suffix = f"-{number:02d}" if number else ""
    return f"{city}/{device_id}/{when:%Y-%m-%d}/{kind}-{when:%H%M%S}{suffix}.{extension}"


def build_scan(device_id: str, city: str, when: datetime, rng: random.Random) -> dict:
    """One scan result. The values are made up; only the shape matters for the labs."""
    return {
        "device_id": device_id,
        "city": city,
        "scanned_at": when.isoformat(timespec="seconds"),
        "items_scanned": rng.randint(20, 200),
        "items_flagged": rng.randint(0, 5),
        "firmware": "1.4.2",
    }


def log_line(when: datetime, level: str, message: str) -> str:
    return f"{when.isoformat(timespec='seconds')} {level:<5} {message}"


def post(url: str, body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode() if body is not None else b""
    request = urllib.request.Request(
        url, data=data, method="POST", headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read() or b"{}")


def run(args: argparse.Namespace) -> int:
    rng = random.Random(args.seed)
    outbox = Path(args.outbox)
    lines: list[str] = []

    status, body = post(
        f"{args.server}/devices",
        {"device_id": args.device_id, "city": args.city, "owner": args.owner},
    )
    if status not in (201, 409):  # 409: registered by an earlier run
        print(f"registration refused: {status} {body.get('detail')}")
        return 1
    print("registered" if status == 201 else "already registered")

    for number in range(1, args.scans + 1):
        now = datetime.now(UTC)
        status, _ = post(f"{args.server}/devices/{args.device_id}/heartbeat")
        lines.append(log_line(now, "INFO", f"heartbeat {status}"))

        scan = build_scan(args.device_id, args.city, now, rng)
        path = outbox / object_key(args.city, args.device_id, now, "scan", number)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(scan, indent=2) + "\n", encoding="utf-8", newline="\n")
        lines.append(log_line(now, "INFO", f"scan {number} written: {scan['items_scanned']} items"))
        print(f"scan {number}: {path.as_posix()}")
        if number < args.scans:
            time.sleep(args.interval)

    now = datetime.now(UTC)
    log_path = outbox / object_key(args.city, args.device_id, now, "log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"log: {log_path.as_posix()}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulated scanner device")
    parser.add_argument("--server", default="http://127.0.0.1:8000")
    parser.add_argument("--device-id", required=True)
    parser.add_argument("--city", required=True)
    parser.add_argument("--owner", default="site-team-a")
    parser.add_argument("--scans", type=int, default=3)
    parser.add_argument("--interval", type=float, default=1.0, help="seconds between scans")
    parser.add_argument("--outbox", default="outbox")
    parser.add_argument("--seed", type=int, default=None)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
