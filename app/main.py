"""HTTP API of the central server. Day 2 starter: register devices, record heartbeats, list them.

Later days add: the device list on an EBS volume (Day 4), uploads to the landing bucket (Day 5),
the device list in a database (Day 6), the dashboard and the Lambda sorter (Day 6, Day 7).
"""

from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import __version__
from app.config import get_settings
from app.registry import Device, DeviceExists, DeviceUnknown, Registry
from app.validation import RegistrationRejected, upload_prefix, validate_registration

app = FastAPI(title="Device Registry", version=__version__)
registry = Registry()


class Registration(BaseModel):
    device_id: str = Field(examples=["scanner-007"])
    city: str = Field(examples=["pune"])
    owner: str = Field(examples=["site-team-a"])


class DeviceView(BaseModel):
    device_id: str
    city: str
    owner: str
    status: str
    registered_at: datetime
    last_seen: datetime | None
    upload_prefix: str


def _view(device: Device) -> DeviceView:
    timeout = get_settings().heartbeat_timeout_seconds
    return DeviceView(
        device_id=device.device_id,
        city=device.city,
        owner=device.owner,
        status=device.status(registry.clock(), timeout),
        registered_at=device.registered_at,
        last_seen=device.last_seen,
        upload_prefix=upload_prefix(device.city, device.device_id),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": __version__,
        "env": get_settings().app_env,
        "heartbeat_timeout_seconds": str(get_settings().heartbeat_timeout_seconds),
    }


@app.post("/devices", response_model=DeviceView, status_code=201)
def register_device(body: Registration) -> DeviceView:
    """Check a registration and add the device to the list."""
    city = body.city.strip().lower()
    try:
        validate_registration(body.device_id, city, body.owner, get_settings())
        device = registry.register(body.device_id, city, body.owner)
    except RegistrationRejected as err:
        raise HTTPException(status_code=422, detail=str(err)) from err
    except DeviceExists as err:
        raise HTTPException(status_code=409, detail="device is already registered") from err
    return _view(device)


@app.post("/devices/{device_id}/heartbeat", response_model=DeviceView)
def heartbeat(device_id: str) -> DeviceView:
    """Record that the device is alive."""
    try:
        return _view(registry.heartbeat(device_id))
    except DeviceUnknown as err:
        raise HTTPException(status_code=404, detail="device is not registered") from err


@app.get("/devices", response_model=list[DeviceView])
def list_devices() -> list[DeviceView]:
    return [_view(device) for device in registry.all()]
