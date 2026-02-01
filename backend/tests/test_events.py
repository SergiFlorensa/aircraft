import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi.testclient import TestClient

from app.db.models import FlightEvent
from app.db.session import get_db
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

    try:
        response = client.post("/events", json=payload)

        assert response.status_code == 202
        data = response.json()
        assert "id" in data
        assert fake_stream.messages, "stream should receive the payload"

        stored_message = fake_stream.messages[0]
        assert stored_message["aircraft_id"] == payload["aircraft_id"]
        assert data["id"] == stored_message["id"]
        assert stored_message["timestamp"].startswith("2024-01-01T12:00:00")
    finally:
        app.dependency_overrides.pop(get_telemetry_stream, None)


class FakeSession:
    def __init__(self, event: FlightEvent | None) -> None:
        self._event = event

    def get(self, model, key):  # noqa: ANN001, D401
        """Return the stored event for tests."""
        return self._event


def test_get_event_by_id_returns_payload() -> None:
    event_id = uuid.uuid4()
    stored_event = FlightEvent(
        id=event_id,
        aircraft_id="EC-MYT",
        timestamp=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        latitude=41.2974,
        longitude=2.0833,
        altitude=12000.0,
        speed=450.0,
        raw_data={"source": "adsb"},
    )

    app.dependency_overrides[get_db] = lambda: FakeSession(stored_event)
    client = TestClient(app)

    try:
        response = client.get(f"/events/{event_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(event_id)
        assert data["aircraft_id"] == "EC-MYT"
        assert data["raw_data"] == {"source": "adsb"}
        assert data["timestamp"].startswith("2024-01-01T12:00:00")
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_get_event_by_id_missing_returns_404() -> None:
    event_id = uuid.uuid4()
    app.dependency_overrides[get_db] = lambda: FakeSession(None)
    client = TestClient(app)

    try:
        response = client.get(f"/events/{event_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Event not found"
    finally:
        app.dependency_overrides.pop(get_db, None)
