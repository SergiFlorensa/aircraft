from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.db.models import FlightEvent
from app.db.session import get_db
from app.services.telemetry_stream import (
    TelemetryStreamPublisher,
    get_telemetry_stream,
)

router = APIRouter(prefix="/events", tags=["events"])


class TelemetryEvent(BaseModel):
    aircraft_id: str = Field(..., min_length=1, max_length=32)
    timestamp: datetime
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    altitude: float = Field(..., ge=0.0)
    speed: float = Field(..., ge=0.0)
    raw_data: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "example": {
                "aircraft_id": "EC-MYT",
                "timestamp": "2024-01-01T12:00:00Z",
                "latitude": 41.2974,
                "longitude": 2.0833,
                "altitude": 12000.0,
                "speed": 450.0,
                "raw_data": {"source": "adsb", "signal": -50},
            }
        }
    }


class TelemetryEventResponse(BaseModel):
    id: uuid.UUID


class TelemetryEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    aircraft_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    altitude: float
    speed: float
    raw_data: dict[str, Any]


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TelemetryEventResponse,
)
def ingest_event(
    payload: TelemetryEvent,
    stream: TelemetryStreamPublisher = Depends(get_telemetry_stream),
) -> TelemetryEventResponse:
    event_id = uuid.uuid4()
    message = payload.model_dump(mode="json")
    message["id"] = str(event_id)
    stream.publish(message)
    return TelemetryEventResponse(id=event_id)


@router.get(
    "/{event_id}",
    response_model=TelemetryEventRead,
    status_code=status.HTTP_200_OK,
)
def get_event(event_id: uuid.UUID, db: Session = Depends(get_db)) -> TelemetryEventRead:
    event = db.get(FlightEvent, event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event
