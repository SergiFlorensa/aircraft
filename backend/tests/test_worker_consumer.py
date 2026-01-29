import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, FlightEvent
from app.workers.telemetry_consumer import TelemetryWorker


def build_session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


class DummyRedis:
    def xgroup_create(self, *args, **kwargs):  # noqa: D401
        """No-op for tests."""

    def xreadgroup(self, *args, **kwargs):  # noqa: D401
        """No-op for tests."""
        return []

    def xack(self, *args, **kwargs):  # noqa: D401
        """No-op for tests."""


TestingSessionLocal = build_session_factory()


def test_worker_persists_payload_into_db() -> None:
    worker = TelemetryWorker(redis_client=DummyRedis())
    worker.session_factory = TestingSessionLocal

    event_id = uuid.uuid4()
    payload = {
        "id": str(event_id),
        "aircraft_id": "EC-MYT",
        "timestamp": datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc).isoformat(),
        "latitude": 41.2974,
        "longitude": 2.0833,
        "altitude": 12000.0,
        "speed": 450.0,
        "raw_data": {"source": "adsb"},
    }

    worker._process_entry({"payload": json.dumps(payload).encode("utf-8")})  # type: ignore[arg-type]

    with TestingSessionLocal() as db:
        stored = db.query(FlightEvent).one()
        assert stored.id == event_id
        assert stored.aircraft_id == "EC-MYT"
        assert stored.raw_data == {"source": "adsb"}