from __future__ import annotations

import json
from collections.abc import Generator
from typing import Any

from redis import Redis

from app.core.config import settings


class TelemetryStreamPublisher:
    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    def publish(self, payload: dict[str, Any]) -> str:
        data = json.dumps(payload).encode("utf-8")
        return self._redis.xadd(settings.redis_stream, {"payload": data})


def get_telemetry_stream() -> Generator[TelemetryStreamPublisher, None, None]:
    client = Redis.from_url(settings.redis_url, decode_responses=False)
    try:
        yield TelemetryStreamPublisher(client)
    finally:
        client.close()