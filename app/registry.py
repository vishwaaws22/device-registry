"""The device list. Day 2 starter: kept in memory, so it is empty after every restart.

Later days move it to a file on an EBS volume (Day 4) and to a database (Day 6).
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime


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


class Registry:
    def __init__(self, clock: Callable[[], datetime] = lambda: datetime.now(UTC)) -> None:
        self._devices: dict[str, Device] = {}
        self.clock = clock

    def register(self, device_id: str, city: str, owner: str) -> Device:
        if device_id in self._devices:
            raise DeviceExists(device_id)
        device = Device(device_id, city, owner, registered_at=self.clock())
        self._devices[device_id] = device
        return device

    def heartbeat(self, device_id: str) -> Device:
        device = self._devices.get(device_id)
        if device is None:
            raise DeviceUnknown(device_id)
        device.last_seen = self.clock()
        return device

    def all(self) -> list[Device]:
        return sorted(self._devices.values(), key=lambda d: d.device_id)

    def clear(self) -> None:
        self._devices.clear()
