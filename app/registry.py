"""The device list.

Without a data file (Day 2) the list is kept in memory and is empty after every restart.
With a data file (Day 4: `DATA_DIR` set, on an EBS-backed directory) every change is written to
`<DATA_DIR>/devices.json` and the list is read back when the server starts.
Day 6 moves it to a database.
"""

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


class DeviceExists(Exception):
    """A device with this id is already registered."""


class DeviceUnknown(Exception):
    """No device with this id is registered."""


@dataclass
class Device:
    device_id: str
    city: str
    owner: str
    registered_at: datetime
    last_seen: datetime | None = None

    def status(self, now: datetime, timeout_seconds: int) -> str:
        """registered: never heard from; online: heartbeat within the timeout; else offline."""
        if self.last_seen is None:
            return "registered"
        age = (now - self.last_seen).total_seconds()
        return "online" if age <= timeout_seconds else "offline"


def _to_json(device: Device) -> dict[str, str | None]:
    return {
        "device_id": device.device_id,
        "city": device.city,
        "owner": device.owner,
        "registered_at": device.registered_at.isoformat(),
        "last_seen": device.last_seen.isoformat() if device.last_seen else None,
    }


def _from_json(item: dict[str, str | None]) -> Device:
    last_seen = item.get("last_seen")
    return Device(
        device_id=str(item["device_id"]),
        city=str(item["city"]),
        owner=str(item["owner"]),
        registered_at=datetime.fromisoformat(str(item["registered_at"])),
        last_seen=datetime.fromisoformat(last_seen) if last_seen else None,
    )


class Registry:
    def __init__(
        self,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        data_file: Path | None = None,
    ) -> None:
        self._devices: dict[str, Device] = {}
        self.clock = clock
        self.data_file = data_file
        if data_file is not None and data_file.exists():
            items = json.loads(data_file.read_text(encoding="utf-8"))
            self._devices = {d.device_id: d for d in map(_from_json, items)}

    def _save(self) -> None:
        """Write the list to a temporary file, then rename it: a crash never leaves half a file."""
        if self.data_file is None:
            return
        tmp = self.data_file.with_suffix(".tmp")
        tmp.write_text(json.dumps([_to_json(d) for d in self.all()], indent=2), encoding="utf-8")
        os.replace(tmp, self.data_file)

    def register(self, device_id: str, city: str, owner: str) -> Device:
        if device_id in self._devices:
            raise DeviceExists(device_id)
        device = Device(device_id, city, owner, registered_at=self.clock())
        self._devices[device_id] = device
        self._save()
        return device

    def heartbeat(self, device_id: str) -> Device:
        device = self._devices.get(device_id)
        if device is None:
            raise DeviceUnknown(device_id)
        device.last_seen = self.clock()
        self._save()
        return device

    def all(self) -> list[Device]:
        return sorted(self._devices.values(), key=lambda d: d.device_id)

    def clear(self) -> None:
        self._devices.clear()
        self._save()
