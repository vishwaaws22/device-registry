"""Day 4: the device list survives a restart when it is kept in a data file."""

import json
from datetime import UTC, datetime

from app.registry import Registry


def fixed_clock() -> datetime:
    return datetime(2026, 11, 26, 9, 0, tzinfo=UTC)


def test_without_a_data_file_the_list_is_memory_only(tmp_path):
    first = Registry(clock=fixed_clock)
    first.register("scanner-007", "pune", "site-team-a")
    assert Registry(clock=fixed_clock).all() == []
    assert list(tmp_path.iterdir()) == []


def test_the_list_is_read_back_after_a_restart(tmp_path):
    data = tmp_path / "devices.json"
    first = Registry(clock=fixed_clock, data_file=data)
    first.register("scanner-007", "pune", "site-team-a")
    first.heartbeat("scanner-007")

    second = Registry(clock=fixed_clock, data_file=data)  # a new process, same file
    [device] = second.all()
    assert device.device_id == "scanner-007"
    assert device.city == "pune"
    assert device.last_seen == fixed_clock()


def test_the_file_is_plain_json_without_a_temporary_file_left(tmp_path):
    data = tmp_path / "devices.json"
    Registry(clock=fixed_clock, data_file=data).register("scanner-008", "mumbai", "site-team-b")
    assert json.loads(data.read_text(encoding="utf-8"))[0]["device_id"] == "scanner-008"
    assert [p.name for p in tmp_path.iterdir()] == ["devices.json"]
