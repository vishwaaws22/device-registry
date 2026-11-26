from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app, registry

client = TestClient(app)

GOOD = {"device_id": "scanner-007", "city": "pune", "owner": "site-team-a"}


class FakeClock:
    def __init__(self) -> None:
        self.now = datetime(2026, 11, 24, 9, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: int) -> None:
        self.now += timedelta(seconds=seconds)


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    registry.clear()
    fake = FakeClock()
    monkeypatch.setattr(registry, "clock", fake)
    return fake


def test_registration_returns_the_upload_prefix():
    response = client.post("/devices", json=GOOD)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "registered"
    assert body["upload_prefix"] == "pune/scanner-007/"
    assert body["last_seen"] is None


def test_the_same_device_cannot_register_twice():
    client.post("/devices", json=GOOD)
    assert client.post("/devices", json=GOOD).status_code == 409


@pytest.mark.parametrize(
    "change",
    [
        {"device_id": "../scanner"},
        {"device_id": "ab"},  # too short
        {"city": "atlantis"},
        {"city": "pune/../mumbai"},
        {"owner": "Site Team"},
    ],
)
def test_bad_registrations_are_rejected(change):
    response = client.post("/devices", json={**GOOD, **change})
    assert response.status_code == 422


def test_heartbeat_makes_the_device_online(clock):
    client.post("/devices", json=GOOD)
    response = client.post("/devices/scanner-007/heartbeat")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_device_goes_offline_after_the_timeout(clock):
    client.post("/devices", json=GOOD)
    client.post("/devices/scanner-007/heartbeat")
    clock.advance(121)
    assert client.get("/devices").json()[0]["status"] == "offline"


def test_heartbeat_of_an_unknown_device_is_refused():
    assert client.post("/devices/scanner-999/heartbeat").status_code == 404


def test_list_is_sorted_by_device_id():
    client.post("/devices", json={**GOOD, "device_id": "scanner-020"})
    client.post("/devices", json={**GOOD, "device_id": "scanner-003", "city": "mumbai"})
    assert [d["device_id"] for d in client.get("/devices").json()] == ["scanner-003", "scanner-020"]
