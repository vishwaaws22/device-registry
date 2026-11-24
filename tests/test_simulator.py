import random
from datetime import UTC, datetime

from simulator.scanner_sim import build_scan, object_key

WHEN = datetime(2026, 11, 24, 9, 5, 7, tzinfo=UTC)


def test_object_key_starts_with_city_and_device():
    assert object_key("pune", "scanner-007", WHEN, "scan", 2) == (
        "pune/scanner-007/2026-11-24/scan-090507-02.json"
    )
    assert object_key("pune", "scanner-007", WHEN, "log").endswith("/log-090507.log")


def test_scan_names_its_device_and_city():
    scan = build_scan("scanner-007", "pune", WHEN, random.Random(1))
    assert scan["device_id"] == "scanner-007"
    assert scan["city"] == "pune"
    assert scan["items_flagged"] <= scan["items_scanned"]
