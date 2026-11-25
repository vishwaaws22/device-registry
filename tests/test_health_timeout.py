from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_reports_the_heartbeat_timeout():
    response = client.get("/health")
    assert response.json()["heartbeat_timeout_seconds"] == "120"
