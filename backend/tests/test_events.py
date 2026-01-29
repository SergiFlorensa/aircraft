from datetime import datetime, timezone
from typing import Any

from fastapi.testclient import TestClient

from app.main import app
from app.services.telemetry_stream import get_telemetry_stream


class FakeTelemetryStream:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    def publish(self, payload: dict[str, Any]) -> str:
        self.messages.append(payload)
        return "1-0"


def test_post_event_enqueues_payload() -> None:
    fake_stream = FakeTelemetryStream()
    app.dependency_overrides[get_telemetry_stream] = lambda: fake_stream
    client = TestClient(app)

    payload = {
        "aircraft_id": "EC-MYT",
        "timestamp": datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc).isoformat(),
        "latitude": 41.2974,
        "longitude": 2.0833,
        "altitude": 12000.0,
        "speed": 450.0,
        "raw_data": {"source": "adsb"},
    }

    response = client.post("/events", json=payload)

    assert response.status_code == 202
    data = response.json()
    assert "id" in data
    assert fake_stream.messages, "stream should receive the payload"

    stored_message = fake_stream.messages[0]
    assert stored_message["aircraft_id"] == payload["aircraft_id"]
    assert data["id"] == stored_message["id"]
    assert stored_message["timestamp"].startswith("2024-01-01T12:00:00")

    app.dependency_overrides.pop(get_telemetry_stream, None)