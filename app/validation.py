"""Server-side checks for a registration. A device in a public network is never trusted."""

import re

from app.config import Settings

_SAFE_DEVICE = re.compile(r"^[a-z0-9][a-z0-9-]{2,39}$")
_SAFE_OWNER = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")


class RegistrationRejected(ValueError):
    """The registration breaks a rule; the message is safe to show to the caller."""


def validate_registration(device_id: str, city: str, owner: str, settings: Settings) -> None:
    if not _SAFE_DEVICE.match(device_id):
        raise RegistrationRejected("device id is not valid")
    if city not in settings.allowed_cities:
        raise RegistrationRejected(f"city {city!r} is not allowed")
    if not _SAFE_OWNER.match(owner):
        raise RegistrationRejected("owner is not valid")


def upload_prefix(city: str, device_id: str) -> str:
    """Where this device may write in the landing bucket: one prefix per city and device."""
    return f"{city}/{device_id}/"
