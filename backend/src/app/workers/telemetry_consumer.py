from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from redis import Redis
from redis.exceptions import ResponseError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import FlightEvent
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class TelemetryWorker:
    def __init__(self, redis_client: Redis) -> None:
        self.redis = redis_client
        self.session_factory = SessionLocal

    def ensure_stream(self) -> None:
        try:
            self.redis.xgroup_create(
                name=settings.redis_stream,
                groupname=settings.redis_consumer_group,
                id="0-0",
                mkstream=True,
            )
        except ResponseError as exc:  # group already exists
            if "BUSYGROUP" not in str(exc):
                raise

    def run_forever(self) -> None:
        self.ensure_stream()
        logger.info("Telemetry worker started", extra={"stream": settings.redis_stream})
        while True:
            response = self.redis.xreadgroup(
                groupname=settings.redis_consumer_group,
                consumername=settings.redis_consumer_name,
                streams={settings.redis_stream: ">"},
                count=32,
                block=settings.redis_block_ms,
            )
            if not response:
                continue

            for _stream_name, entries in response:
                for entry_id, data in entries:
                    try:
                        self._process_entry(data)
                        self.redis.xack(settings.redis_stream, settings.redis_consumer_group, entry_id)
                    except Exception as exc:  # noqa: BLE001
                        logger.exception("Failed to ingest telemetry", extra={"entry_id": entry_id})

    def _process_entry(self, data: dict[str, Any]) -> None:
        raw_payload = data.get("payload")
        if raw_payload is None:
            raw_payload = data.get(b"payload")
        if raw_payload is None:
            logger.warning("Entry missing payload", extra={"data": data})
            return

        if isinstance(raw_payload, bytes):
            raw_payload = raw_payload.decode("utf-8")

        payload = json.loads(raw_payload)
        payload["id"] = uuid.UUID(payload["id"])
        payload["timestamp"] = datetime.fromisoformat(payload["timestamp"])
        payload.setdefault("raw_data", {})

        with self._db_session() as db:
            self._store_event(db, payload)

    def _store_event(self, db: Session, payload: dict[str, Any]) -> None:
        event = FlightEvent(**payload)
        db.add(event)
        db.commit()

    def _db_session(self) -> Session:
        return self.session_factory()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    redis_client = Redis.from_url(settings.redis_url, decode_responses=False)
    worker = TelemetryWorker(redis_client)
    worker.run_forever()


if __name__ == "__main__":
    main()
